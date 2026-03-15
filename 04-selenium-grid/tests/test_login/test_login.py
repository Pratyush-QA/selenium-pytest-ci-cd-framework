"""
tests/test_login/test_login.py — Login page tests
==================================================
CONCEPTS DEMONSTRATED:
  ✔ Page Object Model — tests call page methods, not raw Selenium
  ✔ Fixtures injected as parameters (login_page)
  ✔ @pytest.mark.parametrize for multiple credential combinations
  ✔ Allure steps, severity, feature/story grouping
  ✔ Positive AND negative test scenarios
  ✔ Fluent interface chaining: page.open().login().assert_...

RUN:
    pytest tests/test_login/ -v
    pytest -m login -v
    pytest -m smoke -v
"""

import time

import pytest
import allure

from config.settings import settings
from src.pages.login_page import LoginPage
from src.utils.logger import get_logger

log = get_logger(__name__)


@allure.feature("Login")
@allure.story("Successful Login")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
@pytest.mark.login
def test_valid_login_redirects_and_shows_success(login_page: LoginPage):
    """
    HAPPY PATH: Valid credentials → redirected to /secure, success flash shown.

    AAA Pattern:
      Arrange: login_page fixture provides a fresh page object with new driver
      Act:     open login page, enter credentials, click login
      Assert:  check URL changed and success message is visible
    """
    with allure.step("Open the login page"):
        login_page.open_login_page()
        time.sleep(2)                           # 👁 watch: login page loaded on Grid UI

    with allure.step("Enter valid credentials and submit"):
        login_page.login(settings.valid_username, settings.valid_password)
        time.sleep(2)                           # 👁 watch: credentials typed + submitted

    with allure.step("Assert redirect to /secure"):
        assert "secure" in login_page.get_current_url(), (
            f"Expected URL to contain 'secure', got: {login_page.get_current_url()}"
        )
        time.sleep(2)                           # 👁 watch: /secure page visible on Grid UI

    with allure.step("Assert success flash message is visible"):
        assert login_page.is_logged_in(), "Logout button not visible after login"
        success_msg = login_page.get_success_message()
        allure.attach(success_msg, "Success Message", allure.attachment_type.TEXT)
        assert "You logged into a secure area!" in success_msg
        time.sleep(2)                           # 👁 watch: success flash message visible


@allure.feature("Login")
@allure.story("Logout Flow")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.regression
@pytest.mark.login
def test_logout_after_login(login_page: LoginPage):
    """Login → logout → verify redirected back to login page."""
    with allure.step("Login with valid credentials"):
        login_page.open_login_page().login(
            settings.valid_username, settings.valid_password
        )
        time.sleep(2)                           # 👁 watch: logged in to /secure

    with allure.step("Click Logout"):
        login_page.click_logout()
        time.sleep(2)                           # 👁 watch: logout clicked, redirecting

    with allure.step("Assert redirected back to login page"):
        assert "login" in login_page.get_current_url()
        time.sleep(2)                           # 👁 watch: back on login page

    with allure.step("Assert login form is visible again"):
        assert login_page.is_element_visible(login_page.USERNAME_INPUT), (
            "Username input not visible after logout"
        )
        time.sleep(2)                           # 👁 watch: login form visible again


@allure.feature("Login")
@allure.story("Invalid Login")
@allure.severity(allure.severity_level.CRITICAL)
@pytest.mark.negative
@pytest.mark.login
@pytest.mark.parametrize(
    "username, password, expected_error_fragment",
    [
        (
            "invalidUser",
            "SuperSecretPassword!",
            "Your username is invalid",       # wrong username
        ),
        (
            "tomsmith",
            "WrongPassword",
            "Your password is invalid",       # wrong password
        ),
        (
            "",
            "",
            "Your username is invalid",       # empty credentials
        ),
    ],
    ids=["wrong-username", "wrong-password", "empty-credentials"],
)
def test_invalid_login_shows_error(
    login_page: LoginPage,
    username: str,
    password: str,
    expected_error_fragment: str,
):
    """
    CONCEPT: Parametrize for multiple invalid credential combinations.
    Each parameter set becomes a separate test case in the report.

    3 negative scenarios in 1 test function:
      1. wrong username
      2. wrong password
      3. empty credentials
    """
    with allure.step(f"Attempt login with username='{username}'"):
        login_page.open_login_page().login(username, password)
        time.sleep(2)                           # 👁 watch: invalid credentials typed + submitted

    with allure.step("Assert error message is displayed"):
        assert login_page.is_error_displayed(), "Error message not shown for invalid login"
        time.sleep(2)                           # 👁 watch: error flash message visible on page

    with allure.step(f"Assert error contains: '{expected_error_fragment}'"):
        error_msg = login_page.get_error_message()
        allure.attach(error_msg, "Error Message", allure.attachment_type.TEXT)
        assert expected_error_fragment in error_msg, (
            f"Expected '{expected_error_fragment}' in error, got: '{error_msg}'"
        )
        time.sleep(2)                           # 👁 watch: error text confirmed on Grid UI

    with allure.step("Assert user stays on login page (no redirect)"):
        assert "login" in login_page.get_current_url()
        time.sleep(2)                           # 👁 watch: still on /login, no redirect


@allure.feature("Login")
@allure.story("Page Title")
@pytest.mark.smoke
@pytest.mark.login
def test_login_page_title(login_page: LoginPage):
    """Verify the login page has the correct document title."""
    login_page.open_login_page()
    time.sleep(2)                               # 👁 watch: login page loaded on Grid UI
    title = login_page.get_title()
    assert "The Internet" in title, f"Unexpected page title: '{title}'"
    time.sleep(2)                               # 👁 watch: title verified, test finishing
