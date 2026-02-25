"""
Utah Building Trends Explorer — County Boundaries Layer
Dashed county outlines for geographic context.
"""
import json
import os

import folium


def build_county_boundaries_layer(geojson_path: str) -> folium.FeatureGroup:
    """
    Build a county boundary overlay with dashed outlines and hover tooltips.
    """
    with open(geojson_path, "r") as f:
        geojson_data = json.load(f)

    fg = folium.FeatureGroup(name="County Boundaries", show=True)

    # Determine the county name field from the GeoJSON
    # plotly source uses feature.properties (may have NAME or name)
    # Also, the plotly source often has minimal properties — try to detect
    sample_props = {}
    if geojson_data["features"]:
        sample_props = geojson_data["features"][0].get("properties", {})

    name_field = None
    for candidate in ["NAME", "name", "Name", "NAMELSAD"]:
        if candidate in sample_props:
            name_field = candidate
            break

    style_function = lambda feature: {
        "fillOpacity": 0,
        "color": "#888888",
        "weight": 1.5,
        "dashArray": "5 5",
    }

    if name_field:
        geojson_layer = folium.GeoJson(
            geojson_data,
            name="County Boundaries",
            style_function=style_function,
            tooltip=folium.GeoJsonTooltip(
                fields=[name_field],
                aliases=["County:"],
                style="font-family:Arial,sans-serif;font-size:12px;",
            ),
        )
    else:
        # No name field — use the feature ID (county FIPS) as tooltip
        geojson_layer = folium.GeoJson(
            geojson_data,
            name="County Boundaries",
            style_function=style_function,
        )

    geojson_layer.add_to(fg)
    return fg
