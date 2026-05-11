"""
tests/test_dynamic/test_dynamic_loading.py — Dynamic / AJAX content tests
==========================================================================
CONCEPTS DEMONSTRATED:
  ✔ Explicit waits for AJAX-loaded content
  ✔ wait_for_invisible (loading spinner)
  ✔ wait_for_visible (element appears after load)
  ✔ Parametrize across both examples (hidden vs not-yet-in-DOM)

ActionChains tests also live here: hover reveals hidden content.
"""

import pytest
import allure

from src.pages.dynamic_loading_page import DynamicLoadingPage
from src.pages.hover_page import HoverPage
from src.utils.logger import get_logger

log = get_logger(__name__)


@allure.feature("Dynamic Loading")
@allure.story("Hidden Element Becomes Visible")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.smoke
@pytest.mark.dynamic
def test_dynamic_loading_example1(dynamic_loading_page: DynamicLoadingPage):
    """
    Example 1: element EXISTS in DOM but is hidden → loading reveals it.

    Flow: click Start → bar appears → bar disappears → text visible
    """
    with allure.step("Open dynamic loading example 1"):
        dynamic_loading_page.open_example(1)

    with allure.step("Click Start and wait for loading to complete"):
        result_text = dynamic_loading_page.start_and_wait(timeout=15)
        allure.attach(result_text, "Result Text", allure.attachment_type.TEXT)

    with allure.step("Assert finish text is 'Hello World!'"):
        assert "Hello World!" in result_text, (
            f"Expected 'Hello World!', got: '{result_text}'"
        )


@allure.feature("Dynamic Loading")
@allure.story("Element Added to DOM After Loading")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
@pytest.mark.dynamic
def test_dynamic_loading_example2(dynamic_loading_page: DynamicLoadingPage):
    """
    Example 2: element does NOT exist in DOM → loading adds it.

    CONCEPT: This is a harder case for Selenium.
    EC.presence_of_element_located() and EC.visibility_of_element_located()
    both handle it, but the element must not exist before Start is clicked.
    """
    with allure.step("Open dynamic loading example 2"):
        dynamic_loading_page.open_example(2)

    with allure.step("Click Start and wait for finish element to be added"):
        result_text = dynamic_loading_page.start_and_wait(timeout=15)

    with allure.step("Assert finish text is 'Hello World!'"):
        assert "Hello World!" in result_text


@allure.feature("Dynamic Loading")
@allure.story("Both Examples")
@pytest.mark.regression
@pytest.mark.dynamic
@pytest.mark.parametrize("example", [1, 2], ids=["hidden-element", "element-not-in-dom"])
def test_both_examples_show_hello_world(
    dynamic_loading_page: DynamicLoadingPage, example: int
):
    """
    Parametrized: run both examples in a single test function.
    Verifies both approaches produce the same result text.
    """
    dynamic_loading_page.open_example(example)
    result = dynamic_loading_page.start_and_wait(timeout=15)
    assert "Hello World!" in result, (
        f"Example {example}: Expected 'Hello World!', got '{result}'"
    )


# =============================================================================
# ACTIONCHAINS TESTS — Hover
# =============================================================================

@allure.feature("ActionChains")
@allure.story("Hover to Reveal Content")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.smoke
@pytest.mark.actions
def test_hover_reveals_figure_caption(hover_page: HoverPage):
    """
    CONCEPT: ActionChains.move_to_element()
    ────────────────────────────────────────
    Hover over a figure to trigger CSS :hover state and reveal a
    hidden caption. The caption is hidden with CSS visibility:hidden
    until the mouse is over the element.

    This tests that ActionChains correctly simulates mouse movement.
    """
    with allure.step("Open hovers page"):
        hover_page.open_hover_page()

    with allure.step("Hover over the first figure (index 0)"):
        hover_page.hover_over_figure(0)

    with allure.step("Assert caption text is revealed"):
        caption = hover_page.get_caption_text(0)
        allure.attach(caption, "Caption Text", allure.attachment_type.TEXT)
        assert caption, "Caption should not be empty after hover"
        assert "name" in caption.lower() or "user" in caption.lower(), (
            f"Unexpected caption: '{caption}'"
        )


@allure.feature("ActionChains")
@allure.story("Hover to Reveal Content")
@pytest.mark.regression
@pytest.mark.actions
@pytest.mark.parametrize("figure_index", [0, 1, 2])
def test_hover_all_figures(hover_page: HoverPage, figure_index: int):
    """
    Parametrized: hover each of the 3 figures and verify a caption appears.
    Each figure is a separate test case.
    """
    hover_page.open_hover_page()
    hover_page.hover_over_figure(figure_index)
    caption = hover_page.get_caption_text(figure_index)
    assert caption, f"No caption revealed for figure {figure_index}"
