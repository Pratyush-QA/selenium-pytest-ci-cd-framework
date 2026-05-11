"""
src/pages/checkbox_page.py — Page Object for /checkboxes
=========================================================
URL: https://the-internet.herokuapp.com/checkboxes
Demonstrates: checkbox state queries, check/uncheck actions
"""

from selenium.webdriver.common.by import By
from src.pages.base_page import BasePage
from src.utils.logger import get_logger

log = get_logger(__name__)


class CheckboxPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    # CSS :nth-of-type(n) selects the nth element of that type within parent
    CHECKBOX_1 = (By.CSS_SELECTOR, "form#checkboxes input:nth-of-type(1)")
    CHECKBOX_2 = (By.CSS_SELECTOR, "form#checkboxes input:nth-of-type(2)")
    ALL_CHECKBOXES = (By.CSS_SELECTOR, "form#checkboxes input[type='checkbox']")

    def open_checkbox_page(self) -> "CheckboxPage":
        self.open("checkboxes")
        self.wait_for_visible(self.CHECKBOX_1)
        log.info("Checkbox page opened")
        return self

    def is_checkbox1_checked(self) -> bool:
        return self.is_checked(self.CHECKBOX_1)

    def is_checkbox2_checked(self) -> bool:
        return self.is_checked(self.CHECKBOX_2)

    def check_checkbox1(self) -> "CheckboxPage":
        self.check(self.CHECKBOX_1)
        return self

    def uncheck_checkbox1(self) -> "CheckboxPage":
        self.uncheck(self.CHECKBOX_1)
        return self

    def check_checkbox2(self) -> "CheckboxPage":
        self.check(self.CHECKBOX_2)
        return self

    def uncheck_checkbox2(self) -> "CheckboxPage":
        self.uncheck(self.CHECKBOX_2)
        return self

    def get_all_checkbox_states(self) -> list[bool]:
        """Return a list of checked states for all checkboxes on the page."""
        elements = self.driver.find_elements(*self.ALL_CHECKBOXES)
        return [el.is_selected() for el in elements]
