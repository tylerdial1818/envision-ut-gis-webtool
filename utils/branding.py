"""
Utah Building Trends Explorer — Branding & UI Chrome
Title bar, legend, attribution badge, reset view button, and popup CSS.
"""
import folium

from utils.popup import POPUP_CSS


def build_popup_styles() -> folium.Element:
    """Inject shared CSS classes for popup/tooltip HTML to reduce file size."""
    return folium.Element(POPUP_CSS)


def build_title_bar() -> folium.Element:
    """Fixed-position title bar at the top of the map."""
    html = '''
    <div id="title-bar" style="
        position:fixed; top:0; left:0; right:0; z-index:1000;
        background:rgba(255,255,255,0.95);
        padding:10px 20px;
        box-shadow:0 2px 6px rgba(0,0,0,0.15);
        font-family:Arial,sans-serif;
        max-height:65px; overflow:hidden;
    ">
        <div style="font-size:14px;font-weight:bold;letter-spacing:0.5px;color:#222">
            UTAH BUILDING TRENDS EXPLORER
        </div>
        <div style="font-size:12px;color:#555;margin-top:2px">
            Where is new housing being built? Explore construction patterns
            across Utah&#39;s 2,020 census block groups.
        </div>
        <div style="font-size:11px;color:#999;margin-top:1px">
            Hover to preview &middot; Click for details &middot; Source: ACS 2023
        </div>
    </div>
    '''
    return folium.Element(html)


def build_legend(tiers: list[dict]) -> folium.Element:
    """Discrete legend matching growth tiers, positioned bottom-left."""
    rows = ""
    # Reverse order: highest tier first
    for tier in reversed(tiers):
        pct_min = int(tier["min"] * 100)
        pct_max = int(tier["max"] * 100)
        if tier == tiers[-1]:
            range_str = f"({pct_min}%+)"
        elif tier == tiers[0]:
            range_str = f"(<{pct_max}%)"
        else:
            range_str = f"({pct_min}–{pct_max}%)"
        rows += (
            f'<div style="margin:3px 0">'
            f'<span style="color:{tier["color"]};font-size:16px;'
            f'vertical-align:middle">&#9679;</span> '
            f'<span style="vertical-align:middle">'
            f'{tier["label"]} {range_str}</span></div>\n'
        )

    html = f'''
    <div id="legend" style="
        position:fixed; bottom:30px; left:10px; z-index:1000;
        background:white; padding:12px 16px; border-radius:6px;
        box-shadow:0 1px 4px rgba(0,0,0,0.2);
        font-family:Arial,sans-serif; font-size:12px;
        line-height:1.4; max-width:260px;
    ">
        <div style="font-weight:bold;margin-bottom:6px">
            % Housing Built Since 2020
        </div>
        {rows}
        <div style="color:#888;font-size:11px;margin-top:6px">
            &#9675; larger = more total units
        </div>
    </div>
    '''
    return folium.Element(html)


def build_attribution(text: str = "Powered by <b>SOCIO</b>") -> folium.Element:
    """'Powered by SOCIO' badge in the bottom-right corner."""
    html = f'''
    <div id="attribution" style="
        position:fixed; bottom:10px; right:10px; z-index:1000;
        background:white; padding:6px 12px; border-radius:4px;
        font-family:Arial,sans-serif; font-size:11px; color:#555;
        box-shadow:0 1px 3px rgba(0,0,0,0.2);
    ">{text}</div>
    '''
    return folium.Element(html)


def build_reset_view_button(center: list, zoom: int) -> folium.Element:
    """Button that resets the map to the default Wasatch Front view."""
    lat, lon = center
    html = f'''
    <button id="reset-view-btn" onclick="
        var maps = Object.values(window).filter(function(v) {{
            return v instanceof L.Map;
        }});
        if (maps.length > 0) maps[0].setView([{lat}, {lon}], {zoom});
    " style="
        position:fixed; top:75px; right:10px; z-index:1000;
        background:white; border:1px solid #ccc; border-radius:4px;
        padding:6px 12px; cursor:pointer;
        font-family:Arial,sans-serif; font-size:12px; color:#333;
    " onmouseover="this.style.background='#f0f0f0'"
       onmouseout="this.style.background='white'"
    >&#8635; Reset View</button>
    '''
    return folium.Element(html)
