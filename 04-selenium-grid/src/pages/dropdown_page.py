"""
src/pages/dropdown_page.py — Page Object for /dropdown
=======================================================
URL: https://the-internet.herokuapp.com/dropdown
Demonstrates: Select class, option introspection
"""

from selenium.webdriver.common.by import By
from src.pages.base_page import BasePage
from src.utils.logger import get_logger

log = get_logger(__name__)


class DropdownPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    DROPDOWN = (By.ID, "dropdown")

    def open_dropdown_page(self) -> "DropdownPage":
        self.open("dropdown")
        self.wait_for_visible(self.DROPDOWN)
        log.info("Dropdown page opened")
        return self

    def select_option_by_text(self, text: str) -> "DropdownPage":
        """Select dropdown option by its visible text label."""
        log.info("Selecting option: '%s'", text)
        self.select_by_visible_text(self.DROPDOWN, text)
        return self

    def select_option_by_value(self, value: str) -> "DropdownPage":
        """Select dropdown option by its HTML value attribute."""
        self.select_by_value(self.DROPDOWN, value)
        return self

    def get_selected_option(self) -> str:
        """Return the currently selected option's visible text."""
        return self.get_selected_option_text(self.DROPDOWN)

    def get_all_options(self) -> list[str]:
        """Return all available option labels in the dropdown."""
        return self.get_all_dropdown_options(self.DROPDOWN)
