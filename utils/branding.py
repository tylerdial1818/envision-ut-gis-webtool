"""
Utah Building Trends Explorer — Branding & UI Chrome
Title bar, legend, attribution badge, reset view button, and popup CSS.
"""
import base64
import io
import os

import folium
from PIL import Image

from utils.popup import POPUP_CSS

# Pre-compute base64 logo strings at import time
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_logo_b64(filename: str, height: int) -> str:
    """Load a PNG logo, resize to target height, return base64 data URI."""
    path = os.path.join(_PROJECT_ROOT, filename)
    img = Image.open(path)
    ratio = height / img.height
    new_size = (int(img.width * ratio), height)
    img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return base64.b64encode(buf.getvalue()).decode()


ENVISION_LOGO_B64 = _load_logo_b64("EnvisionUTlogo.png", 70)
SOCIO_LOGO_B64 = _load_logo_b64("SocioLogo.png", 44)


def build_popup_styles() -> folium.Element:
    """Inject shared CSS classes for popup/tooltip HTML to reduce file size."""
    return folium.Element(POPUP_CSS)


def build_title_bar() -> folium.Element:
    """Fixed-position title bar at the top of the map."""
    logo_src = f"data:image/png;base64,{ENVISION_LOGO_B64}"
    html = f'''
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <div id="title-bar" style="
        position:fixed; top:0; left:0; right:0; z-index:1000;
        background:linear-gradient(135deg, rgba(255,255,255,0.97) 0%, rgba(248,250,252,0.97) 100%);
        padding:10px 220px 10px 24px;
        box-shadow:0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.05);
        font-family:'Inter',system-ui,-apple-system,sans-serif;
        max-height:96px; overflow:hidden;
        border-bottom:1px solid rgba(0,0,0,0.06);
        backdrop-filter:blur(8px);
        -webkit-backdrop-filter:blur(8px);
        display:flex; align-items:center; gap:16px;
    ">
        <a href="https://envisionutah.org/" target="_blank" rel="noopener noreferrer"
           style="flex-shrink:0;display:flex;align-items:center">
            <img src="{logo_src}" alt="Envision Utah" style="height:70px;width:auto">
        </a>
        <div style="min-width:0">
            <div style="font-size:19px;font-weight:700;letter-spacing:0.3px;color:#1a1a2e">
                BUILDING TRENDS EXPLORER
            </div>
            <div style="font-size:14px;color:#64748b;margin-top:2px;font-weight:400">
                Where is new housing being built? Explore construction patterns
                across Utah&#39;s 2,020 census block groups.
                <span style="color:#94a3b8;margin-left:6px">Hover circles to preview &middot; Click a circle for details</span>
            </div>
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
            f'<div style="margin:4px 0;display:flex;align-items:center;gap:8px">'
            f'<span style="display:inline-block;width:12px;height:12px;'
            f'border-radius:50%;background:{tier["color"]};'
            f'box-shadow:0 0 0 1px rgba(0,0,0,0.08)"></span>'
            f'<span style="color:#334155;font-size:12px">'
            f'{tier["label"]} <span style="color:#94a3b8">{range_str}</span></span></div>\n'
        )

    html = f'''
    <div id="legend" style="
        position:fixed; bottom:30px; left:10px; z-index:1000;
        background:rgba(255,255,255,0.97); padding:14px 18px; border-radius:10px;
        box-shadow:0 1px 3px rgba(0,0,0,0.08), 0 4px 12px rgba(0,0,0,0.05);
        border:1px solid rgba(0,0,0,0.06);
        font-family:'Inter',system-ui,-apple-system,sans-serif;
        line-height:1.5; max-width:280px;
        backdrop-filter:blur(8px);
        -webkit-backdrop-filter:blur(8px);
    ">
        <div style="font-weight:600;margin-bottom:8px;font-size:13px;color:#1a1a2e">
            % Housing Built Since 2020
        </div>
        {rows}
        <div style="color:#94a3b8;font-size:11px;margin-top:8px;padding-top:8px;border-top:1px solid #f1f5f9">
            &#9675; Larger circle = more total units
        </div>
        <div style="color:#94a3b8;font-size:11px;margin-top:4px">
            Source: ACS 2023 5-Year Estimates
        </div>
    </div>
    '''
    return folium.Element(html)


def build_attribution() -> folium.Element:
    """'Powered by SOCIO' badge in the bottom-right corner."""
    logo_src = f"data:image/png;base64,{SOCIO_LOGO_B64}"
    html = f'''
    <a href="https://www.socio-analytics.com/" target="_blank" rel="noopener noreferrer"
       id="attribution" style="
        display:flex; align-items:center; gap:8px; text-decoration:none;
        position:fixed; bottom:10px; right:10px; z-index:1000;
        background:rgba(255,255,255,0.95); padding:10px 18px; border-radius:8px;
        font-family:'Inter',system-ui,-apple-system,sans-serif; font-size:14px; color:#94a3b8;
        box-shadow:0 1px 3px rgba(0,0,0,0.08);
        border:1px solid rgba(0,0,0,0.06);
        transition:all 0.15s ease;
    " onmouseover="this.style.boxShadow='0 2px 8px rgba(0,0,0,0.15)'"
       onmouseout="this.style.boxShadow='0 1px 3px rgba(0,0,0,0.08)'"
    >Powered by <img src="{logo_src}" alt="Socio" style="height:44px;width:auto;vertical-align:middle"></a>
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
        position:fixed; bottom:16px; left:50%; transform:translateX(-50%); z-index:1000;
        background:rgba(255,255,255,0.95); border:1px solid rgba(0,0,0,0.08);
        border-radius:8px;
        padding:8px 14px; cursor:pointer;
        font-family:'Inter',system-ui,-apple-system,sans-serif;
        font-size:12px; font-weight:500; color:#334155;
        box-shadow:0 1px 3px rgba(0,0,0,0.08);
        transition:all 0.15s ease;
        letter-spacing:0.2px;
    " onmouseover="this.style.background='#f8fafc';this.style.boxShadow='0 2px 6px rgba(0,0,0,0.12)'"
       onmouseout="this.style.background='rgba(255,255,255,0.95)';this.style.boxShadow='0 1px 3px rgba(0,0,0,0.08)'"
    >&#8635; Reset View</button>
    '''
    return folium.Element(html)


def build_popup_autopan() -> folium.Element:
    """Override Leaflet popup defaults to auto-pan the map so popups stay in view."""
    html = '''
    <script>
    L.Popup.mergeOptions({
        autoPan: true,
        autoPanPaddingTopLeft: [60, 120],
        autoPanPaddingBottomRight: [60, 20],
        autoPanSpeed: 10
    });
    </script>
    '''
    return folium.Element(html)


def build_zoom_control_mover() -> folium.Element:
    """Move Leaflet's default zoom control from top-left to top-right, below title bar."""
    html = '''
    <style>
        .leaflet-top.leaflet-left .leaflet-control-zoom {
            display: none !important;
        }
        .leaflet-top.leaflet-right {
            top: 96px !important;
        }
        /* Hide base tile layer from layer control (only one base layer) */
        .leaflet-control-layers-base {
            display: none !important;
        }
    </style>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Wait for map to initialize
        setTimeout(function() {
            var maps = Object.values(window).filter(function(v) {
                return v instanceof L.Map;
            });
            if (maps.length > 0) {
                var map = maps[0];
                // Smoother zoom: half-step increments
                map.options.zoomDelta = 0.5;
                map.options.zoomSnap = 0.5;
                // Remove existing zoom control
                map.zoomControl.remove();
                // Add new zoom control to topright with half-step delta
                L.control.zoom({position: 'topright', zoomDelta: 0.5}).addTo(map);
            }
        }, 300);
    });
    </script>
    '''
    return folium.Element(html)


def build_zoom_radius_scaler(
    scale_min: float = 0.25,
    scale_max: float = 1.4,
    zoom_low: int = 8,
    zoom_high: int = 14,
) -> folium.Element:
    """JS that dynamically scales CircleMarker radii based on current zoom level."""
    html = f'''
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(function() {{
            var maps = Object.values(window).filter(function(v) {{
                return v instanceof L.Map;
            }});
            if (maps.length === 0) return;
            var map = maps[0];
            var markers = [];

            // Collect all CircleMarkers (not Circle polygons)
            map.eachLayer(function(layer) {{
                if (layer.eachLayer) {{
                    layer.eachLayer(function(sub) {{
                        if (sub instanceof L.CircleMarker && !(sub instanceof L.Circle)) {{
                            sub._baseRadius = sub.getRadius();
                            markers.push(sub);
                        }}
                    }});
                }}
            }});

            function scaleMarkers() {{
                var zoom = map.getZoom();
                var t = Math.max(0, Math.min(1, (zoom - {zoom_low}) / ({zoom_high} - {zoom_low})));
                var scale = {scale_min} + t * ({scale_max} - {scale_min});
                for (var i = 0; i < markers.length; i++) {{
                    markers[i].setRadius(markers[i]._baseRadius * scale);
                }}
            }}

            map.on('zoomend', scaleMarkers);
            scaleMarkers();  // Apply immediately on load
        }}, 400);
    }});
    </script>
    '''
    return folium.Element(html)


def build_onboarding_modal() -> folium.Element:
    """Welcome modal shown on first page load with navigation instructions."""
    envision_src = f"data:image/png;base64,{ENVISION_LOGO_B64}"
    socio_src = f"data:image/png;base64,{SOCIO_LOGO_B64}"
    html = f'''
    <div id="onboarding-backdrop" style="
        position:fixed; inset:0; z-index:2000;
        background:rgba(0,0,0,0.4);
        backdrop-filter:blur(4px); -webkit-backdrop-filter:blur(4px);
        display:flex; align-items:center; justify-content:center;
    " onclick="if(event.target===this){{this.style.display='none';sessionStorage.setItem('onboarding_seen','1')}}">
        <div style="
            background:#fff; border-radius:14px; padding:32px 36px;
            max-width:480px; width:90%; box-shadow:0 8px 32px rgba(0,0,0,0.18);
            font-family:'Inter',system-ui,-apple-system,sans-serif;
            line-height:1.6; color:#334155;
        ">
            <div style="font-size:20px;font-weight:700;color:#1a1a2e;margin-bottom:16px">
                Welcome to the Building Trends Explorer
            </div>
            <div style="font-size:14px;margin-bottom:20px">
                <div style="margin-bottom:10px">
                    <b>Pan:</b> Click and drag to move around the map
                </div>
                <div style="margin-bottom:10px">
                    <b>Zoom:</b> Use the +/&minus; buttons, scroll wheel, or pinch gesture (trackpad/mobile)
                </div>
                <div style="margin-bottom:10px">
                    <b>Hover a circle:</b> See a quick preview of that area&#39;s data
                </div>
                <div style="margin-bottom:10px">
                    <b>Click a circle:</b> Open a detailed breakdown with benchmarks
                </div>
                <div style="margin-bottom:10px">
                    <b>Toggle layers:</b> Use the checkboxes in the top-right panel to show/hide data layers
                </div>
            </div>
            <button onclick="
                document.getElementById('onboarding-backdrop').style.display='none';
                sessionStorage.setItem('onboarding_seen','1');
            " style="
                display:block; width:100%; padding:12px;
                background:#0570B0; color:#fff; border:none; border-radius:8px;
                font-family:'Inter',system-ui,-apple-system,sans-serif;
                font-size:15px; font-weight:600; cursor:pointer;
                transition:background 0.15s ease;
            " onmouseover="this.style.background='#034E7B'"
               onmouseout="this.style.background='#0570B0'"
            >Got It</button>
            <div style="
                display:flex; align-items:center; justify-content:center; gap:16px;
                margin-top:20px; padding-top:16px; border-top:1px solid #f1f5f9;
            ">
                <span style="font-size:11px;color:#94a3b8;font-weight:500">Built by</span>
                <img src="{envision_src}" alt="Envision Utah" style="height:36px;width:auto;opacity:0.8">
                <span style="color:#e2e8f0;font-size:16px">&amp;</span>
                <img src="{socio_src}" alt="Socio" style="height:28px;width:auto;opacity:0.8">
            </div>
        </div>
    </div>
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        if (sessionStorage.getItem('onboarding_seen') === '1') {{
            var el = document.getElementById('onboarding-backdrop');
            if (el) el.style.display = 'none';
        }}
    }});
    </script>
    '''
    return folium.Element(html)


def build_mobile_styles() -> folium.Element:
    """Responsive CSS + JS for mobile viewports (<600px). Desktop layout untouched."""
    html = '''
    <style>
    @media (max-width: 600px) {
        /* --- Title bar: compact single-row --- */
        #title-bar {
            padding: 8px 12px !important;
            max-height: 56px !important;
            gap: 10px !important;
        }
        #title-bar img { height: 40px !important; }
        #title-bar div[style*="font-size:19px"] {
            font-size: 14px !important;
        }
        #title-bar div[style*="font-size:14px"][style*="color:#64748b"] {
            display: none !important;
        }

        /* --- Leaflet controls: below shorter title bar --- */
        .leaflet-top.leaflet-right {
            top: 62px !important;
        }

        /* --- Layer control: collapse on mobile --- */
        .leaflet-control-layers {
            max-width: 44px;
            overflow: hidden;
        }
        .leaflet-control-layers:hover,
        .leaflet-control-layers.leaflet-control-layers-expanded {
            max-width: 260px;
            overflow: visible;
        }

        /* --- Zoom control: larger touch targets --- */
        .leaflet-control-zoom a {
            width: 40px !important;
            height: 40px !important;
            line-height: 40px !important;
            font-size: 20px !important;
        }

        /* --- FAQ button: bigger touch target, repositioned --- */
        #faq-btn {
            top: 62px !important;
            left: 8px !important;
            padding: 10px 14px !important;
            font-size: 13px !important;
        }

        /* --- Reset button: bigger touch target on mobile --- */
        #reset-view-btn {
            padding: 10px 14px !important;
            font-size: 13px !important;
        }

        /* --- Legend: collapsed by default, tap to expand --- */
        #legend {
            bottom: 16px !important;
            left: 8px !important;
            max-width: 240px !important;
            padding: 0 !important;
            max-height: 36px;
            overflow: hidden;
            transition: max-height 0.25s ease, padding 0.25s ease;
        }
        #legend.mobile-expanded {
            max-height: 400px;
            padding: 12px 14px !important;
        }
        #legend-toggle {
            display: block !important;
        }
        #legend > :not(#legend-toggle) {
            display: none;
        }
        #legend.mobile-expanded > * {
            display: block !important;
        }
        #legend.mobile-expanded > div[style*="display:flex"] {
            display: flex !important;
        }

        /* --- Attribution: compact --- */
        #attribution {
            padding: 6px 10px !important;
            font-size: 11px !important;
            bottom: 56px !important;
        }
        #attribution img { height: 28px !important; }

        /* --- Tooltips: hide on touch devices (hover doesn't work) --- */
        .leaflet-tooltip {
            display: none !important;
        }

        /* --- Popup: fit mobile screen --- */
        .bt-p { width: auto !important; max-width: 260px; }
        .leaflet-popup-content-wrapper {
            max-width: 280px !important;
        }
        .leaflet-popup-content {
            margin: 8px !important;
        }

        /* --- Modals: tighter padding on mobile --- */
        #onboarding-backdrop > div,
        #faq-backdrop > div {
            padding: 24px 20px !important;
        }
    }

    /* Legend toggle button — hidden on desktop, shown on mobile */
    #legend-toggle {
        display: none;
        width: 100%;
        padding: 8px 14px;
        background: none;
        border: none;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        font-size: 12px;
        font-weight: 600;
        color: #1a1a2e;
        cursor: pointer;
        text-align: left;
    }
    </style>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Mobile legend toggle
        var legend = document.getElementById('legend');
        if (!legend) return;

        var toggle = document.createElement('button');
        toggle.id = 'legend-toggle';
        toggle.innerHTML = '&#9650; Legend';
        toggle.addEventListener('click', function(e) {
            e.stopPropagation();
            legend.classList.toggle('mobile-expanded');
            toggle.innerHTML = legend.classList.contains('mobile-expanded')
                ? '&#9660; Legend' : '&#9650; Legend';
        });
        legend.insertBefore(toggle, legend.firstChild);

        // Adjust autoPan padding for smaller mobile title bar
        if (window.innerWidth <= 600 && typeof L !== 'undefined') {
            L.Popup.mergeOptions({
                autoPanPaddingTopLeft: [20, 70],
                autoPanPaddingBottomRight: [20, 20]
            });
        }
    });
    </script>
    '''
    return folium.Element(html)


def build_faq_button() -> folium.Element:
    """FAQ button (fixed position) that opens a modal explaining the map data."""
    html = '''
    <button id="faq-btn" onclick="document.getElementById('faq-backdrop').style.display='flex'" style="
        position:fixed; top:102px; left:10px; z-index:1000;
        background:rgba(255,255,255,0.95); border:1px solid rgba(0,0,0,0.08);
        border-radius:8px; padding:8px 14px; cursor:pointer;
        font-family:'Inter',system-ui,-apple-system,sans-serif;
        font-size:12px; font-weight:500; color:#334155;
        box-shadow:0 1px 3px rgba(0,0,0,0.08);
        transition:all 0.15s ease;
        letter-spacing:0.2px;
    " onmouseover="this.style.background='#f8fafc';this.style.boxShadow='0 2px 6px rgba(0,0,0,0.12)'"
       onmouseout="this.style.background='rgba(255,255,255,0.95)';this.style.boxShadow='0 1px 3px rgba(0,0,0,0.08)'"
    >&#63; FAQ</button>

    <div id="faq-backdrop" style="
        position:fixed; inset:0; z-index:2000;
        background:rgba(0,0,0,0.4);
        backdrop-filter:blur(4px); -webkit-backdrop-filter:blur(4px);
        display:none; align-items:center; justify-content:center;
    " onclick="if(event.target===this)this.style.display='none'">
        <div style="
            background:#fff; border-radius:14px; padding:32px 36px;
            max-width:520px; width:90%; max-height:80vh; overflow-y:auto;
            box-shadow:0 8px 32px rgba(0,0,0,0.18);
            font-family:'Inter',system-ui,-apple-system,sans-serif;
            line-height:1.6; color:#334155; font-size:14px;
        ">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px">
                <div style="font-size:20px;font-weight:700;color:#1a1a2e">
                    Frequently Asked Questions
                </div>
                <button onclick="document.getElementById('faq-backdrop').style.display='none'" style="
                    background:none; border:none; font-size:22px; cursor:pointer;
                    color:#94a3b8; padding:0 4px; line-height:1;
                ">&times;</button>
            </div>

            <div style="margin-bottom:18px">
                <div style="font-weight:600;color:#1a1a2e;margin-bottom:4px">What am I looking at?</div>
                Each circle represents a <b>Census Block Group</b> &mdash; a small geographic
                area defined by the U.S. Census Bureau, typically containing 600 to 3,000 people.
                Utah has about 2,020 block groups.
            </div>

            <div style="margin-bottom:18px">
                <div style="font-weight:600;color:#1a1a2e;margin-bottom:4px">What do circle sizes mean?</div>
                Larger circles indicate more <b>total housing units</b> in that block group.
                A large circle means a denser residential area; a small one means fewer homes.
            </div>

            <div style="margin-bottom:18px">
                <div style="font-weight:600;color:#1a1a2e;margin-bottom:4px">What do the colors mean?</div>
                Colors show the <b>percentage of housing built since 2020</b>. Darker blue
                means a higher share of new construction (a &ldquo;construction hotspot&rdquo;).
                Light gray means minimal recent building activity.
            </div>

            <div style="margin-bottom:18px">
                <div style="font-weight:600;color:#1a1a2e;margin-bottom:4px">Where does the data come from?</div>
                Housing data comes from the <b>American Community Survey (ACS) 2023 5-Year Estimates</b>,
                published by the U.S. Census Bureau.
                <a href="https://data.census.gov/table/ACSDT5Y2023.B25034" target="_blank" rel="noopener" style="color:#0570B0">
                    View the source dataset (Table B25034)</a>.
            </div>

            <div style="margin-bottom:8px">
                <div style="font-weight:600;color:#1a1a2e;margin-bottom:4px">What is the Opportunity Atlas layer?</div>
                The Opportunity Atlas overlay shows <b>upward economic mobility scores</b> by census tract,
                based on research from Harvard University and the U.S. Census Bureau.
                <a href="https://opportunityinsights.org/paper/the-opportunity-atlas/" target="_blank"
                   rel="noopener" style="color:#0570B0">Learn more at Opportunity Insights</a>.
            </div>
        </div>
    </div>
    '''
    return folium.Element(html)
