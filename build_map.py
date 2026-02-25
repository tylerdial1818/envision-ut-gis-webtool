"""
Utah Building Trends Explorer — Build Script
Phase 2: Full map generation with building trends layer and branding.
"""
import logging
import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import folium
import pandas as pd

from utils.census_api import (
    fetch_acs_data,
    load_gazetteer,
    load_opportunity_atlas,
    load_county_boundaries,
)
from utils.data_prep import build_enriched_dataset, build_county_lookup
from layers.building_trends import build_building_trends_layer
from layers.county_boundaries import build_county_boundaries_layer
from utils.branding import (
    build_title_bar,
    build_legend,
    build_attribution,
    build_reset_view_button,
    build_popup_styles,
)
import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("=== Utah Building Trends Explorer — Data Pipeline ===")

    # 1. Fetch ACS data from Census API
    logger.info("Fetching ACS data from Census API...")
    acs_df = fetch_acs_data(
        vintage=config.ACS_VINTAGE,
        variables=config.ACS_VARIABLES,
        state_fips=config.STATE_FIPS,
        cache_path=config.ACS_CACHE,
    )
    logger.info(f"ACS data: {len(acs_df)} block groups")

    # 2. Load Gazetteer centroids
    logger.info("Loading Gazetteer centroids...")
    gaz_df = load_gazetteer(cache_path=config.GAZETTEER_CACHE)
    logger.info(f"Gazetteer: {len(gaz_df)} block groups")

    # 3. Load Opportunity Atlas data
    logger.info("Loading Opportunity Atlas data...")
    try:
        oa_df = load_opportunity_atlas(cache_path=config.OA_CACHE)
        logger.info(f"Opportunity Atlas: {len(oa_df)} tracts")
    except Exception as e:
        logger.warning(f"Could not load Opportunity Atlas data: {e}")
        oa_df = None

    # 4. Load county boundaries
    logger.info("Loading county boundaries...")
    try:
        county_geojson = load_county_boundaries(cache_path=config.COUNTY_GEOJSON_CACHE)
        logger.info(f"County boundaries: {len(county_geojson['features'])} counties")
    except Exception as e:
        logger.warning(f"Could not load county boundaries: {e}")
        county_geojson = None

    # 5. Build lookup tables
    county_lookup = build_county_lookup()

    # 6. Merge and enrich
    logger.info("Building enriched dataset...")
    enriched_df, state_avg = build_enriched_dataset(
        acs_df=acs_df,
        gazetteer_df=gaz_df,
        county_lookup=county_lookup,
        oa_df=oa_df,
        tiers=config.GROWTH_TIERS,
    )
    logger.info(f"Enriched dataset: {len(enriched_df)} rows")
    logger.info(f"State average % new housing: {state_avg*100:.2f}%")

    # 7. Summary stats
    for tier in config.GROWTH_TIERS:
        count = len(enriched_df[enriched_df["tier_label"] == tier["label"]])
        logger.info(f"  {tier['label']}: {count} block groups")

    logger.info("Phase 1 complete. Data ready for map generation.")

    # === Map Generation (Phase 2) ===
    logger.info("Building map...")

    # Initialize map
    m = folium.Map(
        location=config.DEFAULT_CENTER,
        zoom_start=config.DEFAULT_ZOOM,
        tiles=config.TILE_PROVIDER,
        prefer_canvas=True,
    )

    # Add county boundaries (bottom layer — geographic context)
    county_layer = build_county_boundaries_layer(config.COUNTY_GEOJSON_CACHE)
    county_layer.add_to(m)

    # Add building trends markers (main layer)
    building_layer = build_building_trends_layer(
        df=enriched_df,
        state_avg=state_avg,
        config={
            "min_radius": config.MARKER_MIN_RADIUS,
            "max_radius": config.MARKER_MAX_RADIUS,
        },
    )
    building_layer.add_to(m)

    # Add layer control (for toggling layers)
    folium.LayerControl(collapsed=False).add_to(m)

    # Inject popup CSS and branding elements
    m.get_root().html.add_child(build_popup_styles())
    m.get_root().html.add_child(build_title_bar())
    m.get_root().html.add_child(build_legend(config.GROWTH_TIERS))
    m.get_root().html.add_child(build_attribution())
    m.get_root().html.add_child(
        build_reset_view_button(config.DEFAULT_CENTER, config.DEFAULT_ZOOM)
    )

    # Save
    os.makedirs(config.OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(config.OUTPUT_DIR, "utah_building_trends.html")
    m.save(output_path)

    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    logger.info(f"Map saved to {output_path} ({file_size_mb:.1f} MB)")
    logger.info("Phase 2 complete. Open the HTML file in a browser to review.")


if __name__ == "__main__":
    main()
