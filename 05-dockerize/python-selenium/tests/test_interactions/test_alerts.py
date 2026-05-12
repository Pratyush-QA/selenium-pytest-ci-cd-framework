"""
tests/test_interactions/test_alerts.py — JavaScript Alert tests
================================================================
CONCEPTS: JS alert, confirm (accept/dismiss), prompt with text input
"""

import pytest
import allure

from src.pages.alert_page import AlertPage


@allure.feature("JavaScript Alerts")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.smoke
@pytest.mark.interactions
def test_js_alert_accept(alert_page: AlertPage):
    """
    Trigger a JS Alert and accept it.
    Verify the result message on the page updates correctly.
    """
    with allure.step("Open alerts page"):
        alert_page.open_alert_page()

    with allure.step("Trigger and accept JS Alert"):
        alert_text = alert_page.trigger_and_accept_alert()
        allure.attach(alert_text, "Alert Text", allure.attachment_type.TEXT)
        assert "I am a JS Alert" in alert_text

    with allure.step("Assert result message on page"):
        result = alert_page.get_result_text()
        assert "You successfully clicked an alert" in result


@allure.feature("JavaScript Alerts")
@pytest.mark.regression
@pytest.mark.interactions
def test_js_confirm_accept(alert_page: AlertPage):
    """JS Confirm → click OK → verify result shows 'Ok'."""
    alert_page.open_alert_page()
    alert_text = alert_page.trigger_and_accept_confirm()
    result = alert_page.get_result_text()
    assert "Ok" in result, f"Expected 'Ok' in result, got: '{result}'"


@allure.feature("JavaScript Alerts")
@pytest.mark.regression
@pytest.mark.interactions
def test_js_confirm_dismiss(alert_page: AlertPage):
    """JS Confirm → click Cancel → verify result shows 'Cancel'."""
    alert_page.open_alert_page()
    alert_page.trigger_and_dismiss_confirm()
    result = alert_page.get_result_text()
    assert "Cancel" in result, f"Expected 'Cancel' in result, got: '{result}'"


@allure.feature("JavaScript Alerts")
@pytest.mark.regression
@pytest.mark.interactions
@pytest.mark.parametrize("input_text", ["Hello Pytest!", "12345", "UI Framework Test"])
def test_js_prompt_with_text(alert_page: AlertPage, input_text: str):
    """
    JS Prompt → type text → accept → verify text appears in result.

    CONCEPT: Parametrized to test different text inputs in the prompt.
    Each runs as a separate test case.
    """
    with allure.step("Open alerts page"):
        alert_page.open_alert_page()

    with allure.step(f"Type '{input_text}' into JS Prompt and accept"):
        alert_page.trigger_prompt_and_type(input_text)

    with allure.step("Assert typed text appears in page result"):
        result = alert_page.get_result_text()
        assert input_text in result, (
            f"Expected '{input_text}' in result, got: '{result}'"
        )
