"""
src/pages/login_page.py — Page Object for /login
=================================================
URL: https://the-internet.herokuapp.com/login
Credentials: tomsmith / SuperSecretPassword!

CONCEPT: Locator Strategy
──────────────────────────
Define ALL locators as class-level tuples at the top of the page.
Never scatter By.ID / By.CSS strings inside methods — locators change
frequently and should be updated in ONE place.

Locator types (By.*):
  By.ID              → fastest, most reliable when IDs are stable
  By.NAME            → form fields often have name attributes
  By.CSS_SELECTOR    → flexible, recommended for most cases
  By.XPATH           → powerful but verbose, use as last resort
  By.CLASS_NAME      → use when element has a unique class
  By.TAG_NAME        → rarely used directly
  By.LINK_TEXT       → exact text of <a> links
  By.PARTIAL_LINK_TEXT → partial match on link text
"""

from selenium.webdriver.common.by import By
from src.pages.base_page import BasePage
from src.utils.logger import get_logger

log = get_logger(__name__)

PAGE_PATH = "login"


class LoginPage(BasePage):
    """
    Encapsulates all interactions with the Login page.
    Tests should ONLY call methods on this class — never raw Selenium.
    """

    # ── Locators ──────────────────────────────────────────────────────────────
    # CONCEPT: Storing locators as class constants means:
    #   - One place to update if the UI changes
    #   - Self-documenting: the name tells you what the element IS
    #   - IDE autocomplete works on them
    USERNAME_INPUT  = (By.ID, "username")
    PASSWORD_INPUT  = (By.ID, "password")
    LOGIN_BUTTON    = (By.CSS_SELECTOR, "button[type='submit']")
    SUCCESS_MESSAGE = (By.CSS_SELECTOR, "#flash.success")
    ERROR_MESSAGE   = (By.CSS_SELECTOR, "#flash.error")
    LOGOUT_BUTTON   = (By.CSS_SELECTOR, "a[href='/logout']")

    # ── Page Actions ──────────────────────────────────────────────────────────

    def open_login_page(self) -> "LoginPage":
        """Navigate to the login page."""
        self.open(PAGE_PATH)
        self.wait_for_visible(self.USERNAME_INPUT)
        log.info("Login page opened")
        return self

    def enter_username(self, username: str) -> "LoginPage":
        """Type username into the username field."""
        self.type_text(self.USERNAME_INPUT, username)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        """Type password into the password field."""
        self.type_text(self.PASSWORD_INPUT, password)
        return self

    def click_login(self) -> "LoginPage":
        """Click the Login button."""
        self.click(self.LOGIN_BUTTON)
        return self

    def login(self, username: str, password: str) -> "LoginPage":
        """
        Complete login flow in one call: enter credentials + click login.

        CONCEPT: High-level composite methods hide repetitive steps.
        Tests call login("user", "pass") instead of three separate methods.
        This is the "fluent interface" pattern — each method returns self
        so calls can be chained: page.open().login("user","pass")
        """
        log.info("Logging in as '%s'", username)
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
        return self

    def click_logout(self) -> "LoginPage":
        """Click the Logout button (visible after successful login)."""
        self.click(self.LOGOUT_BUTTON)
        return self

    # ── State Queries ─────────────────────────────────────────────────────────

    def get_success_message(self) -> str:
        """Return the success flash message text."""
        return self.get_text(self.SUCCESS_MESSAGE)

    def get_error_message(self) -> str:
        """Return the error flash message text."""
        return self.get_text(self.ERROR_MESSAGE)

    def is_logged_in(self) -> bool:
        """Return True if the logout button is visible (user is logged in)."""
        return self.is_element_visible(self.LOGOUT_BUTTON)

    def is_error_displayed(self) -> bool:
        """Return True if an error flash message is visible."""
        return self.is_element_visible(self.ERROR_MESSAGE)
