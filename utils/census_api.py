"""
Utah Building Trends Explorer — Data Loading Utilities
Loads block group data from CrimeTable.csv (primary), Census API, Gazetteer,
Opportunity Atlas, and county boundaries.
"""
import io
import json
import logging
import os
import zipfile

import numpy as np
import pandas as pd
import requests

logger = logging.getLogger(__name__)


def load_crime_table(crime_table_path: str, cache_path: str | None = None) -> pd.DataFrame:
    """
    Load block group data from CrimeTable.csv.

    This is the primary data source containing Utah block group demographics,
    housing, crime, and coordinate data from Esri enrichment.

    Returns a DataFrame with standardized column names.
    """
    if cache_path and os.path.exists(cache_path):
        logger.info(f"Loading cached crime table data from {cache_path}")
        df = pd.read_csv(cache_path, dtype={"GEOID": str})
        return df

    logger.info(f"Loading CrimeTable.csv from {crime_table_path}")
    df = pd.read_csv(crime_table_path, encoding="utf-8-sig")

    # Build proper 12-char GEOID from component columns
    df["GEOID"] = (
        df["STATEFP20"].astype(str).str.zfill(2)
        + df["COUNTYFP20"].astype(str).str.zfill(3)
        + df["TRACTCE20"].astype(str).str.zfill(6)
        + df["BLKGRPCE20"].astype(str).str.zfill(1)
    )

    # Verify GEOID length
    bad_geoids = df[df["GEOID"].str.len() != 12]
    if len(bad_geoids) > 0:
        logger.warning(f"{len(bad_geoids)} rows have non-12-char GEOIDs")

    # Rename columns to internal names
    rename_map = {
        "INTPTLAT20": "lat",
        "INTPTLON20": "lon",
        "populationtotals_TOTPOP_CY": "total_pop",
        "householdincome_MEDHINC_CY": "median_hh_income",
        "housingunittotals_TOTHU_CY": "total_housing_units",
        "homevalue_MEDVAL_CY": "median_home_value",
        "OwnerRenter_OWNER_CY": "owner_occupied",
        "OwnerRenter_RENTER_CY": "renter_occupied",
        "unitsinstructure_ACSUNT10": "units_10_19",
        "unitsinstructure_ACSUNT20": "units_20_49",
        "unitsinstructure_ACSUNT50UP": "units_50_plus",
        "yearbuilt_ACSBLT2020": "built_2020_plus",
        "yearbuilt_ACSBLT2010": "built_2010_2019",
        "yearbuilt_ACSBLT2000": "built_2000_2009",
        "educationalattainment_BACHDEG_C": "bachelors",
        "educationalattainment_GRADDEG_C": "grad_degree",
        # Crime fields
        "crime_CRMCYTOTC": "crime_total",
        "crime_CRMCYMVEH": "crime_motor_vehicle",
        "crime_CRMCYLARC": "crime_larceny",
        "crime_CRMCYBURG": "crime_burglary",
        "crime_CRMCYPROC": "crime_property",
        "crime_CRMCYASST": "crime_assault",
        "crime_CRMCYROBB": "crime_robbery",
        "crime_CRMCYRAPE": "crime_rape",
        "crime_CRMCYMURD": "crime_murder",
        "crime_CRMCYPERC": "crime_personal",
        # Additional useful fields
        "gender_MEDAGE_CY": "median_age",
        "populationtotals_POPDENS_CY": "pop_density",
        "Wealth_MEDNW_CY": "median_net_worth",
        "EmploymentUnemployment_UNEMPRT_": "unemployment_rate",
        "KeyUSFacts_POPGRWCYFY": "pop_growth_rate",
        "KeyUSFacts_PCI_CY": "per_capita_income",
        "raceandhispanicorigin_DIVINDX_C": "diversity_index",
        "maritalstatustotals_MARRIED_CY": "married_count",
        "Highway_NEAR_DIST": "highway_distance",
    }
    df = df.rename(columns=rename_map)

    # The CrimeTable doesn't have separate masters/professional/doctorate columns.
    # grad_degree is the combined graduate degree count.
    # Set masters = grad_degree, professional_degree = 0, doctorate = 0 for compatibility.
    df["masters"] = df.get("grad_degree", 0)
    df["professional_degree"] = 0
    df["doctorate"] = 0

    # Keep relevant columns
    keep_cols = ["GEOID", "lat", "lon", "total_pop", "median_hh_income",
                 "total_housing_units", "median_home_value", "owner_occupied",
                 "renter_occupied", "units_10_19", "units_20_49", "units_50_plus",
                 "built_2020_plus", "built_2010_2019", "built_2000_2009",
                 "bachelors", "masters", "professional_degree", "doctorate",
                 "crime_total", "crime_motor_vehicle", "crime_larceny",
                 "crime_burglary", "crime_property", "crime_assault",
                 "crime_robbery", "crime_rape", "crime_murder", "crime_personal",
                 "median_age", "pop_density", "median_net_worth",
                 "unemployment_rate", "pop_growth_rate", "per_capita_income",
                 "diversity_index", "married_count", "highway_distance"]
    existing_cols = [c for c in keep_cols if c in df.columns]
    df = df[existing_cols]

    # Convert numeric columns
    numeric_cols = [c for c in df.columns if c not in ("GEOID",)]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Replace Census sentinel values
    df = df.replace(-666666666, np.nan)

    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        df.to_csv(cache_path, index=False)
        logger.info(f"Cached crime table data to {cache_path}")

    logger.info(f"Loaded {len(df)} block groups from CrimeTable.csv")
    return df


def fetch_acs_data(vintage: int, variables: dict, state_fips: str,
                   api_key: str | None = None, cache_path: str | None = None) -> pd.DataFrame:
    """
    Pull ACS 5-Year block group data for a state from the Census API.

    If cache_path exists and the file is present, loads from cache.
    Otherwise fetches from Census API, caches, and returns.
    """
    if cache_path and os.path.exists(cache_path):
        logger.info(f"Loading cached ACS data from {cache_path}")
        df = pd.read_csv(cache_path, dtype={"GEOID": str})
        return df

    # Resolve API key
    if api_key is None:
        api_key = os.environ.get("CENSUS_API_KEY")

    var_codes = list(variables.keys())
    var_str = ",".join(var_codes)

    url = (
        f"https://api.census.gov/data/{vintage}/acs/acs5"
        f"?get=NAME,{var_str}"
        f"&for=block+group:*&in=state:{state_fips}&in=county:*&in=tract:*"
    )
    if api_key:
        url += f"&key={api_key}"

    logger.info(f"Fetching ACS data from Census API (vintage {vintage})...")
    resp = requests.get(url, timeout=120)
    if resp.status_code != 200:
        raise ValueError(
            f"Census API returned status {resp.status_code}: {resp.text[:500]}"
        )

    data = resp.json()
    headers = data[0]
    rows = data[1:]
    df = pd.DataFrame(rows, columns=headers)

    # Build GEOID: state(2) + county(3) + tract(6) + block_group(1) = 12 chars
    df["GEOID"] = (
        df["state"].str.zfill(2)
        + df["county"].str.zfill(3)
        + df["tract"].str.zfill(6)
        + df["block group"].str.zfill(1)
    )

    bad_geoids = df[df["GEOID"].str.len() != 12]
    if len(bad_geoids) > 0:
        logger.warning(f"{len(bad_geoids)} GEOIDs are not 12 characters")

    # Rename variable codes to friendly names
    df = df.rename(columns=variables)

    # Convert numeric columns
    for col in variables.values():
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Replace Census sentinel values
    df = df.replace(-666666666, np.nan)

    # Drop API geography columns, keep GEOID + NAME + variable columns
    drop_cols = ["state", "county", "tract", "block group"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    if cache_path:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        df.to_csv(cache_path, index=False)
        logger.info(f"Cached ACS data to {cache_path}")

    return df


def load_gazetteer(cache_path: str, state_fips: str = "49") -> pd.DataFrame:
    """
    Load Census 2020 block group centroids (GEOID, lat, lon).

    The Census Bureau does not publish a block group gazetteer file.
    We extract centroids from CrimeTable.csv which contains official
    Census INTPTLAT20/INTPTLON20 internal point coordinates for all
    Utah block groups. Falls back to TIGER/Line shapefile if needed.
    """
    if os.path.exists(cache_path):
        logger.info(f"Loading cached Gazetteer data from {cache_path}")
        df = pd.read_csv(cache_path, dtype={"geoid": str})
        return df

    # Primary source: CrimeTable.csv with official Census internal points
    crime_table_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "..", "CrimeTable.csv"
    )

    if os.path.exists(crime_table_path):
        logger.info(f"Extracting block group centroids from CrimeTable.csv...")
        raw_df = pd.read_csv(crime_table_path, encoding="utf-8-sig")

        # Build proper 12-char GEOID from component columns
        raw_df["geoid"] = (
            raw_df["STATEFP20"].astype(str).str.zfill(2)
            + raw_df["COUNTYFP20"].astype(str).str.zfill(3)
            + raw_df["TRACTCE20"].astype(str).str.zfill(6)
            + raw_df["BLKGRPCE20"].astype(str).str.zfill(1)
        )
        gaz_df = raw_df[["geoid", "INTPTLAT20", "INTPTLON20"]].copy()
        gaz_df = gaz_df.rename(columns={
            "INTPTLAT20": "lat",
            "INTPTLON20": "lon",
        })
    else:
        # Fallback: download TIGER/Line block group shapefile
        url = (
            "https://www2.census.gov/geo/tiger/TIGER2020/BG/"
            f"tl_2020_{state_fips}_bg.zip"
        )
        logger.info(f"Downloading TIGER block group shapefile from {url}...")
        try:
            resp = requests.get(url, timeout=180)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(
                f"Failed to download TIGER block groups from {url}: {e}"
            )

        import tempfile
        import geopandas as gpd
        with tempfile.NamedTemporaryFile(suffix=".zip") as tmp:
            tmp.write(resp.content)
            tmp.flush()
            gdf = gpd.read_file(f"zip://{tmp.name}")

        gdf["centroid"] = gdf.geometry.centroid
        gaz_df = pd.DataFrame({
            "geoid": gdf["GEOID"].astype(str).str.zfill(12),
            "lat": gdf["centroid"].y,
            "lon": gdf["centroid"].x,
        })

    # Filter to state and normalize
    gaz_df = gaz_df[gaz_df["geoid"].str.startswith(state_fips)].copy()
    gaz_df["geoid"] = gaz_df["geoid"].str.zfill(12)
    gaz_df["lat"] = pd.to_numeric(gaz_df["lat"], errors="coerce")
    gaz_df["lon"] = pd.to_numeric(gaz_df["lon"], errors="coerce")

    # Cache
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    gaz_df.to_csv(cache_path, index=False)
    logger.info(f"Cached {len(gaz_df)} Gazetteer rows to {cache_path}")

    return gaz_df


def load_opportunity_atlas(cache_path: str) -> pd.DataFrame:
    """
    Download and load Opportunity Atlas tract-level mobility data.
    Filter to Utah (state == 49).
    """
    if os.path.exists(cache_path):
        logger.info(f"Loading cached Opportunity Atlas data from {cache_path}")
        df = pd.read_csv(cache_path, dtype={"tract_fips": str})
        return df

    url = "https://opportunityinsights.org/wp-content/uploads/2018/10/tract_outcomes_simple.csv"
    logger.info(f"Downloading Opportunity Atlas data from {url}...")

    try:
        resp = requests.get(url, timeout=180)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to download Opportunity Atlas data from {url}: {e}")

    df = pd.read_csv(io.StringIO(resp.text))

    # Filter to Utah (state == 49)
    df = df[df["state"] == 49].copy()

    # Build the full 11-char tract FIPS: state(2) + county(3) + tract(6)
    if "kfr_pooled_pooled_p25" in df.columns:
        df = df[["state", "county", "tract", "kfr_pooled_pooled_p25"]].copy()
        df = df.rename(columns={
            "kfr_pooled_pooled_p25": "mobility_score",
        })
    else:
        logger.warning("Column 'kfr_pooled_pooled_p25' not found in Opportunity Atlas data")
        df = df[["state", "county", "tract"]].copy()
        df["mobility_score"] = np.nan

    # Construct full tract FIPS: state(2) + county(3) + tract(6) = 11 chars
    df["tract_fips"] = (
        df["state"].astype(int).astype(str).str.zfill(2)
        + df["county"].astype(int).astype(str).str.zfill(3)
        + df["tract"].astype(int).astype(str).str.zfill(6)
    )
    df = df[["tract_fips", "mobility_score"]]

    # Cache
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    df.to_csv(cache_path, index=False)
    logger.info(f"Cached {len(df)} Opportunity Atlas tracts to {cache_path}")

    return df


def load_county_boundaries(cache_path: str, state_fips: str = "49") -> dict:
    """
    Download simplified county boundary GeoJSON for Utah.
    Uses the plotly datasets GeoJSON source (single JSON, no shapefile deps).
    """
    if os.path.exists(cache_path):
        logger.info(f"Loading cached county boundaries from {cache_path}")
        with open(cache_path, "r") as f:
            return json.load(f)

    url = "https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json"
    logger.info(f"Downloading county boundaries from {url}...")

    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to download county boundaries from {url}: {e}")

    national = resp.json()

    # Filter to Utah counties (FIPS starts with state_fips)
    utah_features = [
        f for f in national["features"]
        if f.get("id", "").startswith(state_fips)
    ]

    utah_geojson = {
        "type": "FeatureCollection",
        "features": utah_features,
    }

    logger.info(f"Filtered to {len(utah_features)} Utah county boundaries")

    # Cache
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w") as f:
        json.dump(utah_geojson, f)
    logger.info(f"Cached county boundaries to {cache_path}")

    return utah_geojson


def load_tract_boundaries(cache_dir: str, state_fips: str = "49") -> str:
    """
    Download Utah tract shapefile from Census TIGER and return the
    path to the extracted .shp file.

    Source: https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_49_tract_500k.zip
    """
    shp_dir = os.path.join(cache_dir, "utah_tracts")
    # Look for an existing .shp file
    if os.path.exists(shp_dir):
        shp_files = [f for f in os.listdir(shp_dir) if f.endswith(".shp")]
        if shp_files:
            shp_path = os.path.join(shp_dir, shp_files[0])
            logger.info(f"Using cached tract shapefile at {shp_path}")
            return shp_path

    url = f"https://www2.census.gov/geo/tiger/GENZ2020/shp/cb_2020_{state_fips}_tract_500k.zip"
    logger.info(f"Downloading tract boundaries from {url}...")

    try:
        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"Failed to download tract boundaries from {url}: {e}")

    os.makedirs(shp_dir, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        zf.extractall(shp_dir)

    shp_files = [f for f in os.listdir(shp_dir) if f.endswith(".shp")]
    if not shp_files:
        raise ValueError(f"No .shp file found in {shp_dir} after extraction")

    shp_path = os.path.join(shp_dir, shp_files[0])
    logger.info(f"Extracted tract shapefile to {shp_path}")
    return shp_path
