"""Tests to validate the generated HTML map."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import config

OUTPUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", config.OUTPUT_DIR, "utah_building_trends.html"
)


@pytest.fixture(scope="module")
def html_content():
    if not os.path.exists(OUTPUT_PATH):
        pytest.skip("HTML output not found — run build_map.py first")
    with open(OUTPUT_PATH, "r") as f:
        return f.read()


def test_html_file_exists():
    """The output HTML file should exist after running build_map.py."""
    assert os.path.exists(OUTPUT_PATH), f"Expected file at {OUTPUT_PATH}"


def test_html_file_size():
    """HTML file should be between 500KB and 10MB.

    2,020 markers with popup + tooltip HTML typically produces 4-8 MB.
    """
    if not os.path.exists(OUTPUT_PATH):
        pytest.skip("HTML output not found")
    size = os.path.getsize(OUTPUT_PATH)
    assert 500_000 < size < 10_000_000, f"File size {size/1e6:.1f}MB outside expected range"


def test_html_contains_leaflet(html_content):
    """HTML should reference Leaflet (loaded from CDN)."""
    assert "leaflet" in html_content.lower()


def test_html_contains_tier_colors(html_content):
    """HTML should contain all tier colors from config."""
    for tier in config.GROWTH_TIERS:
        assert tier["color"].lower() in html_content.lower(), (
            f"Missing tier color {tier['color']}"
        )


def test_html_contains_branding(html_content):
    """HTML should contain SOCIO attribution and title bar."""
    assert "SOCIO" in html_content
    assert "BUILDING TRENDS" in html_content.upper()
    assert "ACS 2023" in html_content or "ACS" in html_content


def test_html_contains_layer_control(html_content):
    """HTML should contain layer control for toggling."""
    assert (
        "LayerControl" in html_content
        or "leaflet-control-layers" in html_content.lower()
        or "control.layers" in html_content.lower()
    )


def test_marker_count_in_html(html_content):
    """HTML should contain roughly 2,020 circle markers."""
    marker_count = html_content.lower().count("circlemarker")
    assert marker_count > 1000, f"Only found {marker_count} circle marker references"


def test_html_no_nan_display(html_content):
    """The HTML should not contain visible 'nan' or 'NaN' strings in popup content."""
    assert "nan%" not in html_content.lower()
    assert "$nan" not in html_content.lower()
    assert "$-1" not in html_content
