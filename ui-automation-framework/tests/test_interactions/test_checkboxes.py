"""
tests/test_interactions/test_checkboxes.py — Checkbox tests
============================================================
CONCEPTS: checkbox state, check/uncheck idempotency, is_selected()
"""

import pytest
import allure

from src.pages.checkbox_page import CheckboxPage


@allure.feature("Checkboxes")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.smoke
@pytest.mark.interactions
def test_initial_checkbox_state(checkbox_page: CheckboxPage):
    """
    Verify default state on page load.
    On the-internet: checkbox1=unchecked, checkbox2=checked by default.
    """
    with allure.step("Open checkbox page"):
        checkbox_page.open_checkbox_page()

    with allure.step("Assert checkbox 1 is unchecked by default"):
        assert not checkbox_page.is_checkbox1_checked(), "Checkbox 1 should start unchecked"

    with allure.step("Assert checkbox 2 is checked by default"):
        assert checkbox_page.is_checkbox2_checked(), "Checkbox 2 should start checked"


@allure.feature("Checkboxes")
@pytest.mark.regression
@pytest.mark.interactions
def test_check_and_uncheck_checkbox1(checkbox_page: CheckboxPage):
    """Toggle checkbox 1: check it, verify, uncheck it, verify."""
    checkbox_page.open_checkbox_page()

    with allure.step("Check checkbox 1"):
        checkbox_page.check_checkbox1()
        assert checkbox_page.is_checkbox1_checked(), "Checkbox 1 should be checked"

    with allure.step("Uncheck checkbox 1"):
        checkbox_page.uncheck_checkbox1()
        assert not checkbox_page.is_checkbox1_checked(), "Checkbox 1 should be unchecked"


@allure.feature("Checkboxes")
@pytest.mark.regression
@pytest.mark.interactions
def test_check_is_idempotent(checkbox_page: CheckboxPage):
    """
    Calling check() on an already-checked checkbox should be a no-op.

    CONCEPT: Idempotency — calling the same operation multiple times
    should leave the system in the same state as calling it once.
    Our check() helper only clicks if not already checked.
    """
    checkbox_page.open_checkbox_page()

    # checkbox2 starts checked
    checkbox_page.check_checkbox2()  # no-op — already checked
    assert checkbox_page.is_checkbox2_checked(), "Double-check should still be checked"

    # Calling check() again should not uncheck it
    checkbox_page.check_checkbox2()
    assert checkbox_page.is_checkbox2_checked(), "Triple-check should still be checked"


@allure.feature("Checkboxes")
@pytest.mark.regression
@pytest.mark.interactions
def test_all_checkboxes_state_list(checkbox_page: CheckboxPage):
    """Verify we can read all checkbox states as a list."""
    checkbox_page.open_checkbox_page()
    states = checkbox_page.get_all_checkbox_states()
    assert len(states) == 2, f"Expected 2 checkboxes, found {len(states)}"
    assert states == [False, True], f"Expected [False, True], got {states}"
