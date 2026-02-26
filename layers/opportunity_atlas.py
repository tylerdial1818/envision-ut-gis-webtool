"""
Utah Building Trends Explorer — Opportunity Atlas Overlay
Tract-level polygon choropleth showing upward mobility scores.
"""
import json
import logging
import os

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import branca.colormap as cm

logger = logging.getLogger(__name__)


def build_opportunity_atlas_layer(
    enriched_df: pd.DataFrame,
    tract_geojson_path: str | None = None,
) -> tuple[folium.FeatureGroup, folium.Element | None]:
    """
    Build Opportunity Atlas overlay as tract-level colored polygons.

    Uses Census TIGER tract boundary shapefile joined with mobility scores.
    Returns (FeatureGroup, colormap_element).
    """
    import config
    from utils.census_api import load_tract_boundaries

    # 1. Load tract shapefile
    if tract_geojson_path and os.path.exists(tract_geojson_path):
        shp_path = tract_geojson_path
    else:
        shp_path = load_tract_boundaries(
            cache_dir=config.CACHE_DIR,
            state_fips=config.STATE_FIPS,
        )

    logger.info(f"Loading tract geometries from {shp_path}...")
    tracts_gdf = gpd.read_file(shp_path)

    # Normalize GEOID to 11-char tract FIPS
    if "GEOID" in tracts_gdf.columns:
        tracts_gdf["tract_fips"] = tracts_gdf["GEOID"].astype(str).str.zfill(11)
    elif "GEOID20" in tracts_gdf.columns:
        tracts_gdf["tract_fips"] = tracts_gdf["GEOID20"].astype(str).str.zfill(11)
    else:
        raise ValueError(f"No GEOID column found in shapefile. Columns: {tracts_gdf.columns.tolist()}")

    # 2. Aggregate mobility scores to tract level
    if "tract_fips" in enriched_df.columns and "mobility_score" in enriched_df.columns:
        tract_scores = (
            enriched_df.groupby("tract_fips")["mobility_score"]
            .first()
            .reset_index()
        )
    else:
        # Try loading from the OA cache directly
        oa_path = os.path.join(config.CACHE_DIR, "opportunity_atlas.csv")
        if os.path.exists(oa_path):
            tract_scores = pd.read_csv(oa_path, dtype={"tract_fips": str})
        else:
            logger.warning("No mobility scores available for OA layer")
            tract_scores = pd.DataFrame(columns=["tract_fips", "mobility_score"])

    tract_scores["tract_fips"] = tract_scores["tract_fips"].astype(str).str.zfill(11)

    # 3. Merge scores into tract geometries
    tracts_gdf = tracts_gdf.merge(
        tract_scores, on="tract_fips", how="left"
    )
    logger.info(
        f"OA overlay: {tracts_gdf['mobility_score'].notna().sum()}/{len(tracts_gdf)} "
        f"tracts have mobility scores"
    )

    # 4. Build color scale
    valid_scores = tracts_gdf["mobility_score"].dropna()
    if len(valid_scores) > 0:
        vmin = float(valid_scores.quantile(0.05))
        vmax = float(valid_scores.quantile(0.95))
    else:
        vmin, vmax = 0.3, 0.6

    colormap = cm.LinearColormap(
        colors=config.OA_COLOR_SCALE,
        vmin=vmin,
        vmax=vmax,
        caption="Upward Mobility Score (Opportunity Atlas)",
    )

    # 5. Convert to GeoJSON for Folium
    # Reproject to WGS84 if needed
    if tracts_gdf.crs and tracts_gdf.crs.to_epsg() != 4326:
        tracts_gdf = tracts_gdf.to_crs(epsg=4326)

    # Simplify geometry to reduce file size
    tracts_gdf["geometry"] = tracts_gdf["geometry"].simplify(
        tolerance=0.001, preserve_topology=True
    )

    geojson_data = json.loads(tracts_gdf.to_json())

    # 6. Build the FeatureGroup
    fg = folium.FeatureGroup(
        name="Upward Mobility (Opportunity Atlas)",
        show=False,  # Hidden by default
    )

    no_data_color = "#F0F0F0"

    def style_function(feature):
        score = feature["properties"].get("mobility_score")
        if score is None or (isinstance(score, float) and np.isnan(score)):
            fill_color = no_data_color
        else:
            fill_color = colormap(score)
        return {
            "fillColor": fill_color,
            "fillOpacity": config.OA_FILL_OPACITY,
            "color": "#666",
            "weight": 0.3,
            "opacity": config.OA_LINE_OPACITY,
        }

    def tooltip_fn(feature):
        score = feature["properties"].get("mobility_score")
        if score is None or (isinstance(score, float) and np.isnan(score)):
            return "Upward Mobility Score: No data"
        return f"Upward Mobility Score: {score:.3f}"

    geojson_layer = folium.GeoJson(
        geojson_data,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(
            fields=["mobility_score"],
            aliases=["Mobility Score:"],
            style="font-family:Arial,sans-serif;font-size:12px;",
            localize=True,
        ),
    )
    geojson_layer.add_to(fg)

    # Position the colormap legend
    colormap.add_to(fg)

    return fg, None  # colormap is added directly to fg
