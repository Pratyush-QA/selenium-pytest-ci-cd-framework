"""
tests/test_interactions/test_dropdowns.py — Dropdown tests
===========================================================
CONCEPTS DEMONSTRATED:
  ✔ Selenium Select class (select_by_visible_text, select_by_value)
  ✔ Allure steps
  ✔ Parametrize for multiple option selections
"""

import pytest
import allure

from src.pages.dropdown_page import DropdownPage
from src.utils.logger import get_logger

log = get_logger(__name__)


@allure.feature("Dropdown")
@allure.story("Select Options")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.smoke
@pytest.mark.interactions
def test_dropdown_has_correct_options(dropdown_page: DropdownPage):
    """Verify the dropdown contains the expected option labels."""
    with allure.step("Open dropdown page"):
        dropdown_page.open_dropdown_page()

    with allure.step("Get all available options"):
        options = dropdown_page.get_all_options()
        allure.attach(str(options), "All Options", allure.attachment_type.TEXT)

    with allure.step("Assert options include Option 1 and Option 2"):
        assert "Option 1" in options, f"Option 1 not found. Actual: {options}"
        assert "Option 2" in options, f"Option 2 not found. Actual: {options}"


@allure.feature("Dropdown")
@allure.story("Select Options")
@pytest.mark.regression
@pytest.mark.interactions
@pytest.mark.parametrize("option_text", ["Option 1", "Option 2"])
def test_select_dropdown_option_by_text(dropdown_page: DropdownPage, option_text: str):
    """
    Select each option by visible text and verify it becomes selected.
    Parametrized to run once for each option.
    """
    with allure.step("Open dropdown page"):
        dropdown_page.open_dropdown_page()

    with allure.step(f"Select '{option_text}'"):
        dropdown_page.select_option_by_text(option_text)

    with allure.step(f"Assert '{option_text}' is the selected option"):
        selected = dropdown_page.get_selected_option()
        assert selected == option_text, (
            f"Expected '{option_text}' to be selected, got '{selected}'"
        )


@allure.feature("Dropdown")
@allure.story("Select Options")
@pytest.mark.regression
@pytest.mark.interactions
@pytest.mark.parametrize("value, expected_text", [("1", "Option 1"), ("2", "Option 2")])
def test_select_dropdown_option_by_value(
    dropdown_page: DropdownPage, value: str, expected_text: str
):
    """Select by HTML value attribute and verify displayed text."""
    dropdown_page.open_dropdown_page()
    dropdown_page.select_option_by_value(value)
    selected = dropdown_page.get_selected_option()
    assert selected == expected_text, (
        f"After selecting value='{value}', expected '{expected_text}', got '{selected}'"
    )
