"""
Utah Building Trends Explorer — Configuration
All configuration: API, colors, tiers, map defaults, file paths.
"""
import os

# --- Census API Configuration ---
ACS_VINTAGE = 2023  # Latest ACS 5-Year (released Dec 2024, covers 2019-2023)
STATE_FIPS = "49"   # Utah
CENSUS_API_KEY = os.environ.get("CENSUS_API_KEY", None)

# Variables to pull from ACS. Format: {api_variable: friendly_name}
ACS_VARIABLES = {
    # Year Structure Built (Table B25034)
    "B25034_001E": "total_housing_units",
    "B25034_002E": "built_2020_plus",
    "B25034_003E": "built_2010_2019",
    "B25034_004E": "built_2000_2009",
    # Units in Structure (Table B25024)
    "B25024_001E": "total_units_in_structure",
    "B25024_008E": "units_10_19",
    "B25024_009E": "units_20_49",
    "B25024_010E": "units_50_plus",
    # Median Home Value (Table B25077)
    "B25077_001E": "median_home_value",
    # Tenure (Table B25003)
    "B25003_002E": "owner_occupied",
    "B25003_003E": "renter_occupied",
    # Demographics
    "B01003_001E": "total_pop",
    "B19013_001E": "median_hh_income",
    "B15003_022E": "bachelors",
    "B15003_023E": "masters",
    "B15003_024E": "professional_degree",
    "B15003_025E": "doctorate",
}

# --- Growth Tier Classification ---
# Tiers based on % of housing stock built since 2020
GROWTH_TIERS = [
    {"label": "Minimal new construction", "min": 0.00, "max": 0.01, "color": "#D9D9D9"},
    {"label": "Some new construction",    "min": 0.01, "max": 0.03, "color": "#A6BDDB"},
    {"label": "Moderate growth",          "min": 0.03, "max": 0.07, "color": "#3690C0"},
    {"label": "High growth",              "min": 0.07, "max": 0.15, "color": "#0570B0"},
    {"label": "Construction hotspot",     "min": 0.15, "max": 1.00, "color": "#034E7B"},
]

# --- Map Defaults ---
DEFAULT_CENTER = [40.65, -111.9]  # Wasatch Front
DEFAULT_ZOOM = 10
TILE_PROVIDER = "cartodbpositron"

# --- Marker Sizing ---
MARKER_MIN_RADIUS = 3
MARKER_MAX_RADIUS = 15

# --- File Paths ---
CACHE_DIR = "data/cache"
REFERENCE_DIR = "data/reference"
OUTPUT_DIR = "output"
GAZETTEER_CACHE = f"{CACHE_DIR}/gazetteer_ut.csv"
ACS_CACHE = f"{CACHE_DIR}/acs_housing.csv"
OA_CACHE = f"{CACHE_DIR}/opportunity_atlas.csv"
COUNTY_GEOJSON_CACHE = f"{CACHE_DIR}/utah_counties.geojson"
ENRICHED_OUTPUT = f"{CACHE_DIR}/block_groups_enriched.csv"
COUNTY_LOOKUP = f"{REFERENCE_DIR}/county_fips_lookup.csv"
