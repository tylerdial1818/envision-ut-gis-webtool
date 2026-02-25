"""
Utah Building Trends Explorer — Tooltip and Popup HTML Generation
Transforms raw data rows into styled HTML for Leaflet tooltips and popups.
"""
import math


# CSS classes injected once into the page (via branding.py build_popup_styles)
# to keep per-marker HTML small.
POPUP_CSS = """
<style>
.bt-p{font-family:Arial,sans-serif;width:280px;font-size:13px;line-height:1.5;margin:0;padding:0}
.bt-h{color:#fff;padding:8px 12px;border-radius:6px 6px 0 0;font-size:11px;font-weight:bold;letter-spacing:.5px;text-transform:uppercase}
.bt-b{padding:10px 12px}
.bt-sl{font-size:11px;color:#555;text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px}
.bt-d{border-top:1px solid #eee;margin:8px 0}
.bt-v{font-size:12px;line-height:1.6}
.bt-m{color:#888;font-size:11px}
.bt-bar{background:#eee;height:8px;border-radius:3px;margin-bottom:4px}
.bt-tt{font-family:Arial,sans-serif;font-size:12px;padding:4px 8px;max-width:200px;line-height:1.4}
</style>
"""


def format_value(value, prefix="", suffix="", na_sentinel=-1) -> str:
    """Helper to format numeric values with N/A handling."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    try:
        num = float(value)
        if num == na_sentinel and na_sentinel is not None:
            return "N/A"
        if prefix == "$":
            return f"${int(num):,}"
        if suffix == "%":
            return f"{num:.0f}%"
        return f"{prefix}{int(num):,}{suffix}"
    except (ValueError, TypeError):
        return "N/A"


def build_tooltip_html(row: dict, county_name: str) -> str:
    """Lightweight hover tooltip. Compact 3-line display."""
    pct = row.get("pct_new_housing", 0) or 0
    tier_color = row.get("tier_color", "#CCCCCC")
    total_units = int(row.get("total_housing_units", 0) or 0)

    return (
        f'<div class="bt-tt">'
        f'<b>{county_name}</b><br>'
        f'<span style="color:{tier_color};font-size:14px">&#9632;</span> '
        f'{pct*100:.1f}% new construction<br>'
        f'<span class="bt-m">{total_units:,} total units</span></div>'
    )


def build_popup_html(row: dict, county_name: str, state_avg: float) -> str:
    """Full data card shown on click with tier badge, progress bar, benchmarks."""
    tier_label = row.get("tier_label", "No data")
    tier_color = row.get("tier_color", "#CCCCCC")
    pct_new = row.get("pct_new_housing", 0) or 0
    built_2020 = int(row.get("built_2020_plus", 0) or 0)
    total_units = int(row.get("total_housing_units", 0) or 0)
    built_2010 = int(row.get("built_2010_2019", 0) or 0)
    built_2000 = int(row.get("built_2000_2009", 0) or 0)
    units_10_plus = int(row.get("units_10_plus", 0) or 0)
    units_50_plus = int(row.get("units_50_plus", 0) or 0)
    pct_renter = row.get("pct_renter", 0) or 0
    name = row.get("NAME", "")

    mv = format_value(row.get("median_home_value"), prefix="$")
    mi = format_value(row.get("median_hh_income"), prefix="$")
    bar_pct = min(pct_new / 0.20, 1.0) * 100

    return (
        f'<div class="bt-p">'
        f'<div class="bt-h" style="background:{tier_color}">{tier_label}</div>'
        f'<div class="bt-b">'
        f'<div class="bt-m">{county_name} County</div>'
        f'<div style="font-weight:bold;margin-bottom:8px">{name}</div>'
        f'<div class="bt-sl">New Construction</div>'
        f'<div class="bt-bar"><div style="background:{tier_color};height:8px;border-radius:3px;width:{bar_pct:.0f}%"></div></div>'
        f'<div><b>{pct_new*100:.1f}%</b> built since 2020 ({built_2020:,} units)</div>'
        f'<div class="bt-m">State average: {state_avg*100:.1f}%</div>'
        f'<div class="bt-d"></div>'
        f'<div class="bt-sl">Housing Profile</div>'
        f'<div class="bt-v">Total units: {total_units:,}<br>'
        f'Built 2010\u20132019: {built_2010:,}<br>'
        f'Built 2000\u20132009: {built_2000:,}<br>'
        f'In 10+ unit bldgs: {units_10_plus:,}<br>'
        f'In 50+ unit bldgs: {units_50_plus:,}</div>'
        f'<div class="bt-d"></div>'
        f'<div class="bt-sl">Market Context</div>'
        f'<div class="bt-v">Median home value: {mv}<br>'
        f'Renter-occupied: {pct_renter*100:.0f}%<br>'
        f'Median HH income: {mi}</div>'
        f'</div></div>'
    )
