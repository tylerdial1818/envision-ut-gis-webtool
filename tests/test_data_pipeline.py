"""
Utah Building Trends Explorer — Data Pipeline Tests
Validates the enriched dataset output from Phase 1.
"""
import json
import os
import sys

import pandas as pd
import pytest

# Ensure project root is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config

ENRICHED_PATH = os.path.join(
    os.path.dirname(__file__), "..", config.ENRICHED_OUTPUT
)
COUNTY_GEOJSON_PATH = os.path.join(
    os.path.dirname(__file__), "..", config.COUNTY_GEOJSON_CACHE
)


@pytest.fixture(scope="module")
def enriched_df():
    """Load the enriched dataset for testing."""
    if not os.path.exists(ENRICHED_PATH):
        pytest.skip("Enriched dataset not found — run build_map.py first")
    df = pd.read_csv(ENRICHED_PATH, dtype={"GEOID": str})
    return df


@pytest.fixture(scope="module")
def county_geojson():
    """Load the county GeoJSON for testing."""
    if not os.path.exists(COUNTY_GEOJSON_PATH):
        pytest.skip("County GeoJSON not found — run build_map.py first")
    with open(COUNTY_GEOJSON_PATH, "r") as f:
        return json.load(f)


def test_row_count(enriched_df):
    """Enriched dataset should have between 1,900 and 2,100 rows (expect ~2,020)."""
    assert 1900 <= len(enriched_df) <= 2100, (
        f"Expected ~2,020 rows, got {len(enriched_df)}"
    )


def test_geoid_format(enriched_df):
    """All GEOIDs should be 12-character strings starting with '49'."""
    for geoid in enriched_df["GEOID"]:
        assert isinstance(geoid, str), f"GEOID {geoid} is not a string"
        assert len(geoid) == 12, f"GEOID {geoid} is not 12 characters (len={len(geoid)})"
        assert geoid.startswith("49"), f"GEOID {geoid} does not start with '49'"


def test_no_null_coordinates(enriched_df):
    """No rows should have NaN lat or lon."""
    assert enriched_df["lat"].notna().all(), "Found NaN values in lat column"
    assert enriched_df["lon"].notna().all(), "Found NaN values in lon column"


def test_derived_fields_range(enriched_df):
    """pct_new_housing, pct_renter, pct_college should all be in [0, 1]."""
    for col in ["pct_new_housing", "pct_renter", "pct_college"]:
        assert col in enriched_df.columns, f"Missing column: {col}"
        vals = enriched_df[col].dropna()
        assert (vals >= 0).all(), f"{col} has values < 0"
        assert (vals <= 1).all(), f"{col} has values > 1"


def test_growth_tier_coverage(enriched_df):
    """Every row should have a non-null tier_label and tier_color."""
    assert enriched_df["tier_label"].notna().all(), "Found NaN tier_label"
    assert enriched_df["tier_color"].notna().all(), "Found NaN tier_color"
    # Verify tier labels are from our config
    valid_labels = {t["label"] for t in config.GROWTH_TIERS} | {"No data"}
    actual_labels = set(enriched_df["tier_label"].unique())
    assert actual_labels.issubset(valid_labels), (
        f"Unexpected tier labels: {actual_labels - valid_labels}"
    )


def test_county_name_coverage(enriched_df):
    """No rows should have 'Unknown County' (all should map to real county names)."""
    unknown = enriched_df[enriched_df["county_name"] == "Unknown County"]
    assert len(unknown) == 0, (
        f"{len(unknown)} rows have 'Unknown County'. "
        f"County FIPS: {unknown['county_fips'].unique().tolist()}"
    )


def test_state_average_reasonable(enriched_df):
    """State average pct_new_housing should be between 0.005 and 0.15 (0.5%-15%)."""
    if "state_avg_pct_new" in enriched_df.columns:
        avg = enriched_df["state_avg_pct_new"].iloc[0]
    else:
        total_new = enriched_df["built_2020_plus"].sum()
        total_units = enriched_df["total_housing_units"].sum()
        avg = total_new / total_units if total_units > 0 else 0
    assert 0.005 <= avg <= 0.15, (
        f"State average {avg:.4f} ({avg*100:.2f}%) is outside expected range"
    )


def test_opportunity_atlas_join(enriched_df):
    """At least 60% of block groups should have a non-null mobility_score after join.

    Note: OA uses 2010 Census tracts while CrimeTable uses 2020 Census tracts.
    Many tracts were split/renumbered between censuses, so ~70% match is expected.
    """
    if "mobility_score" not in enriched_df.columns:
        pytest.skip("mobility_score column not present (Opportunity Atlas not loaded)")
    matched = enriched_df["mobility_score"].notna().sum()
    total = len(enriched_df)
    pct = matched / total
    assert pct >= 0.60, (
        f"Only {pct*100:.1f}% of block groups have mobility_score (expected >= 60%)"
    )


def test_county_boundaries_valid(county_geojson):
    """County GeoJSON should have exactly 29 features (29 Utah counties)."""
    assert len(county_geojson["features"]) == 29, (
        f"Expected 29 county features, got {len(county_geojson['features'])}"
    )


def test_no_negative_counts(enriched_df):
    """Housing unit counts (built_2020_plus, etc.) should never be negative."""
    count_cols = ["built_2020_plus", "built_2010_2019", "built_2000_2009",
                  "total_housing_units", "units_10_19", "units_20_49", "units_50_plus"]
    for col in count_cols:
        if col in enriched_df.columns:
            vals = enriched_df[col].dropna()
            assert (vals >= 0).all(), f"{col} has negative values"
