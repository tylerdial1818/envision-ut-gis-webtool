"""Final integration tests for the complete tool."""
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


def test_opportunity_atlas_layer_present(html_content):
    """HTML should contain Opportunity Atlas layer references."""
    assert "Upward Mobility" in html_content or "Opportunity Atlas" in html_content


def test_three_toggleable_layers(html_content):
    """Layer control should have three toggleable layers."""
    assert "Building Trends" in html_content
    assert "County Boundaries" in html_content or "County" in html_content
    assert "Mobility" in html_content or "Opportunity" in html_content


def test_deployment_docs_exist():
    """DEPLOYMENT.md and REFRESH.md should exist."""
    project_root = os.path.join(os.path.dirname(__file__), "..")
    assert os.path.exists(os.path.join(project_root, "DEPLOYMENT.md"))
    assert os.path.exists(os.path.join(project_root, "REFRESH.md"))


def test_html_valid_structure(html_content):
    """HTML file should have valid basic structure."""
    assert html_content.strip().startswith("<!DOCTYPE html>") or html_content.strip().startswith("<html")
    assert "</html>" in html_content
    assert "<head>" in html_content
    assert "<body>" in html_content


def test_no_python_errors_in_html(html_content):
    """HTML should not contain Python error traces or unrendered template variables."""
    assert "Traceback" not in html_content
    assert "KeyError" not in html_content
    assert "{row[" not in html_content


def test_file_size_under_budget():
    """Final HTML should be under 10 MB."""
    if not os.path.exists(OUTPUT_PATH):
        pytest.skip("HTML output not found")
    size = os.path.getsize(OUTPUT_PATH)
    mb = size / (1024 * 1024)
    assert mb < 10.0, f"File is {mb:.1f} MB — over the 10 MB budget"


def test_all_tier_colors_present(html_content):
    """All five tier colors should appear in the HTML."""
    content_lower = html_content.lower()
    for tier in config.GROWTH_TIERS:
        color = tier["color"].lower()
        assert color in content_lower, f"Tier color {color} ({tier['label']}) not found in HTML"


def test_state_average_displayed(html_content):
    """The popup template should include a state average benchmark."""
    assert "State average" in html_content or "state average" in html_content
