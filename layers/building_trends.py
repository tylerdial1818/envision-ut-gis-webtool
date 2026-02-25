"""
Utah Building Trends Explorer — Building Trends Layer
Circle markers colored by growth tier, sized by total housing units.
"""
import math

import folium
import pandas as pd

from utils.popup import build_tooltip_html, build_popup_html


def build_building_trends_layer(
    df: pd.DataFrame,
    state_avg: float,
    config: dict,
) -> folium.FeatureGroup:
    """
    Build the primary building trends FeatureGroup with circle markers.

    Each marker is colored by growth tier and sized by log of total housing units.
    Tooltips show a compact preview; popups show the full data card.
    """
    min_radius = config.get("min_radius", 3)
    max_radius = config.get("max_radius", 15)

    fg = folium.FeatureGroup(
        name="Building Trends (% New Construction)",
        show=True,
    )

    for _, row in df.iterrows():
        lat = row.get("lat")
        lon = row.get("lon")
        if pd.isna(lat) or pd.isna(lon):
            continue

        tier_color = row.get("tier_color", "#CCCCCC")
        total_units = row.get("total_housing_units", 0) or 0
        county_name = row.get("county_name", "Unknown")

        # Radius: log-scaled by total housing units
        radius = max(min_radius, min(max_radius, math.log1p(total_units) * 1.5))

        tooltip_html = build_tooltip_html(row.to_dict(), county_name)
        popup_html = build_popup_html(row.to_dict(), county_name, state_avg)

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color=tier_color,
            weight=0.5,
            fill=True,
            fill_color=tier_color,
            fill_opacity=0.7,
            tooltip=folium.Tooltip(tooltip_html),
            popup=folium.Popup(popup_html, max_width=320),
        ).add_to(fg)

    return fg
