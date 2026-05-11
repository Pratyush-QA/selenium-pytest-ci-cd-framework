"""
src/pages/alert_page.py — Page Object for /javascript_alerts
=============================================================
URL: https://the-internet.herokuapp.com/javascript_alerts
Demonstrates: JS alert, confirm, prompt — all 3 alert types
"""

from selenium.webdriver.common.by import By
from src.pages.base_page import BasePage
from src.utils.logger import get_logger

log = get_logger(__name__)


class AlertPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    BTN_ALERT   = (By.XPATH, "//button[text()='Click for JS Alert']")
    BTN_CONFIRM = (By.XPATH, "//button[text()='Click for JS Confirm']")
    BTN_PROMPT  = (By.XPATH, "//button[text()='Click for JS Prompt']")
    RESULT_TEXT = (By.ID, "result")

    def open_alert_page(self) -> "AlertPage":
        self.open("javascript_alerts")
        self.wait_for_visible(self.BTN_ALERT)
        log.info("Alert page opened")
        return self

    def trigger_and_accept_alert(self) -> str:
        """Click the JS Alert button, accept it, return alert text."""
        log.info("Triggering JS Alert")
        self.click(self.BTN_ALERT)
        return self.accept_alert()

    def trigger_and_accept_confirm(self) -> str:
        """Click JS Confirm, accept it (OK), return alert text."""
        log.info("Triggering JS Confirm → accept")
        self.click(self.BTN_CONFIRM)
        return self.accept_alert()

    def trigger_and_dismiss_confirm(self) -> str:
        """Click JS Confirm, dismiss it (Cancel), return alert text."""
        log.info("Triggering JS Confirm → dismiss")
        self.click(self.BTN_CONFIRM)
        return self.dismiss_alert()

    def trigger_prompt_and_type(self, text: str) -> str:
        """Click JS Prompt, type text into it, accept, return prompt text."""
        log.info("Triggering JS Prompt, typing: '%s'", text)
        self.click(self.BTN_PROMPT)
        return self.type_in_prompt(text)

    def get_result_text(self) -> str:
        """Return the result message shown after alert interaction."""
        return self.get_text(self.RESULT_TEXT)
