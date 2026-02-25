"""
Utah Building Trends Explorer — Data Preparation
Merge, derive fields, classify growth tiers, and clean data.
"""
import logging
import os

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default path for county lookup
_DEFAULT_LOOKUP = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data", "reference", "county_fips_lookup.csv"
)


def build_county_lookup(lookup_path: str | None = None) -> dict:
    """
    Build a mapping of 5-digit county FIPS -> county name for Utah's 29 counties.
    Loads from county_fips_lookup.csv if available, otherwise constructs programmatically.
    """
    if lookup_path is None:
        lookup_path = _DEFAULT_LOOKUP

    if os.path.exists(lookup_path):
        df = pd.read_csv(lookup_path, dtype={"county_fips": str})
        lookup = dict(zip(df["county_fips"], df["county_name"]))
        logger.info(f"Loaded {len(lookup)} county mappings from {lookup_path}")
        return lookup

    # Programmatic fallback — Utah's 29 counties
    utah_counties = {
        "49001": "Beaver",    "49003": "Box Elder", "49005": "Cache",
        "49007": "Carbon",    "49009": "Daggett",   "49011": "Davis",
        "49013": "Duchesne",  "49015": "Emery",     "49017": "Garfield",
        "49019": "Grand",     "49021": "Iron",       "49023": "Juab",
        "49025": "Kane",      "49027": "Millard",    "49029": "Morgan",
        "49031": "Piute",     "49033": "Rich",       "49035": "Salt Lake",
        "49037": "San Juan",  "49039": "Sanpete",    "49041": "Sevier",
        "49043": "Summit",    "49045": "Tooele",     "49047": "Uintah",
        "49049": "Utah",      "49051": "Wasatch",    "49053": "Washington",
        "49055": "Wayne",     "49057": "Weber",
    }
    logger.info(f"Built {len(utah_counties)} county mappings programmatically")
    return utah_counties


def county_fips_from_geoid(geoid: str) -> str:
    """Extract 5-char county FIPS from a 12-char GEOID."""
    return geoid[:5]


def classify_growth_tier(pct_new: float, tiers: list[dict]) -> tuple[str, str]:
    """
    Given a pct_new_housing value and the GROWTH_TIERS config,
    return (tier_label, tier_color).
    """
    if pd.isna(pct_new) or pct_new < 0:
        return ("No data", "#CCCCCC")

    for tier in tiers:
        if tier == tiers[-1]:
            # Last tier: use <= for max to catch 100%
            if tier["min"] <= pct_new <= tier["max"]:
                return (tier["label"], tier["color"])
        else:
            if tier["min"] <= pct_new < tier["max"]:
                return (tier["label"], tier["color"])

    return ("No data", "#CCCCCC")


def build_enriched_dataset(
    acs_df: pd.DataFrame,
    gazetteer_df: pd.DataFrame | None = None,
    county_lookup: dict | None = None,
    oa_df: pd.DataFrame | None = None,
    tiers: list[dict] | None = None,
) -> tuple[pd.DataFrame, float]:
    """
    Merge all data sources and compute derived fields.

    ACS data is joined with Gazetteer centroids on GEOID to get lat/lon.
    Opportunity Atlas mobility scores are joined on tract FIPS.

    Returns: (enriched DataFrame, state_avg_pct_new)
    """
    if county_lookup is None:
        county_lookup = build_county_lookup()

    if tiers is None:
        from config import GROWTH_TIERS
        tiers = GROWTH_TIERS

    df = acs_df.copy()

    # --- Step 1: Merge with Gazetteer if needed ---
    if gazetteer_df is not None and "lat" not in df.columns:
        gaz = gazetteer_df.copy()
        # Normalize join keys
        if "geoid" in gaz.columns:
            gaz = gaz.rename(columns={"geoid": "GEOID"})
        gaz["GEOID"] = gaz["GEOID"].astype(str).str.zfill(12)
        df["GEOID"] = df["GEOID"].astype(str).str.zfill(12)

        pre_merge = len(df)
        df = df.merge(gaz[["GEOID", "lat", "lon"]], on="GEOID", how="inner")
        post_merge = len(df)
        if pre_merge != post_merge:
            logger.warning(
                f"Gazetteer merge: {pre_merge} ACS rows -> {post_merge} merged rows "
                f"({pre_merge - post_merge} unmatched)"
            )
    elif gazetteer_df is not None and "lat" in df.columns:
        logger.info("lat/lon already in dataset, skipping Gazetteer merge")

    logger.info(f"Dataset has {len(df)} rows after merge")

    # --- Step 2: County name from GEOID ---
    df["GEOID"] = df["GEOID"].astype(str).str.zfill(12)
    df["county_fips"] = df["GEOID"].apply(county_fips_from_geoid)
    df["county_name"] = df["county_fips"].map(county_lookup).fillna("Unknown County")

    unknown_count = (df["county_name"] == "Unknown County").sum()
    if unknown_count > 0:
        logger.warning(f"{unknown_count} rows mapped to 'Unknown County'")

    # --- Step 3: Derived fields ---
    # Ensure numeric
    for col in ["built_2020_plus", "total_housing_units", "renter_occupied",
                 "owner_occupied", "bachelors", "masters", "professional_degree",
                 "doctorate", "total_pop", "units_10_19", "units_20_49", "units_50_plus"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # pct_new_housing
    df["pct_new_housing"] = np.where(
        df["total_housing_units"] > 0,
        df["built_2020_plus"] / df["total_housing_units"],
        0.0
    )

    # pct_renter
    tenure_denom = df["owner_occupied"] + df["renter_occupied"]
    df["pct_renter"] = np.where(
        tenure_denom > 0,
        df["renter_occupied"] / tenure_denom,
        0.0
    )

    # pct_college
    college_total = df["bachelors"] + df["masters"] + df["professional_degree"] + df["doctorate"]
    df["pct_college"] = np.where(
        df["total_pop"] > 0,
        college_total / df["total_pop"],
        0.0
    )

    # units_10_plus
    df["units_10_plus"] = df["units_10_19"] + df["units_20_49"] + df["units_50_plus"]

    # --- Step 4: Growth tier classification ---
    tier_results = df["pct_new_housing"].apply(lambda x: classify_growth_tier(x, tiers))
    df["tier_label"] = tier_results.apply(lambda x: x[0])
    df["tier_color"] = tier_results.apply(lambda x: x[1])

    # --- Step 5: State-level benchmark (weighted average) ---
    total_built_2020 = df["built_2020_plus"].sum()
    total_units = df["total_housing_units"].sum()
    state_avg_pct_new = total_built_2020 / total_units if total_units > 0 else 0.0
    df["state_avg_pct_new"] = state_avg_pct_new

    # --- Step 6: Opportunity Atlas join ---
    if oa_df is not None:
        df["tract_fips"] = df["GEOID"].str[:11]
        oa = oa_df.copy()
        oa["tract_fips"] = oa["tract_fips"].astype(str).str.zfill(11)
        pre = len(df)
        df = df.merge(oa[["tract_fips", "mobility_score"]], on="tract_fips", how="left")
        matched = df["mobility_score"].notna().sum()
        logger.info(f"Opportunity Atlas join: {matched}/{pre} block groups matched ({matched/pre*100:.1f}%)")

    # --- Step 7: Handle display-ready formatting ---
    if "median_home_value" in df.columns:
        df["median_home_value"] = df["median_home_value"].fillna(-1)
    if "median_hh_income" in df.columns:
        df["median_hh_income"] = df["median_hh_income"].fillna(-1)

    # Drop rows without coordinates
    null_coords = df[df["lat"].isna() | df["lon"].isna()]
    if len(null_coords) > 0:
        logger.warning(f"Dropping {len(null_coords)} rows with missing lat/lon")
        df = df.dropna(subset=["lat", "lon"])

    # --- Step 8: Save ---
    from config import ENRICHED_OUTPUT
    os.makedirs(os.path.dirname(ENRICHED_OUTPUT), exist_ok=True)
    df.to_csv(ENRICHED_OUTPUT, index=False)
    logger.info(f"Saved enriched dataset ({len(df)} rows) to {ENRICHED_OUTPUT}")

    return df, state_avg_pct_new
