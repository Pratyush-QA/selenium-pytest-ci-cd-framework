"""
src/pages/dynamic_loading_page.py — Page Object for /dynamic_loading
=====================================================================
URL: https://the-internet.herokuapp.com/dynamic_loading/1
     https://the-internet.herokuapp.com/dynamic_loading/2

Example 1: element hidden, becomes visible after loading
Example 2: element added to DOM after loading

Demonstrates: waiting for AJAX/dynamic content using explicit waits
"""

from selenium.webdriver.common.by import By
from src.pages.base_page import BasePage
from src.utils.logger import get_logger

log = get_logger(__name__)


class DynamicLoadingPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    START_BUTTON  = (By.CSS_SELECTOR, "#start button")
    LOADING_BAR   = (By.ID, "loading")
    FINISH_TEXT   = (By.ID, "finish")

    def open_example(self, example_number: int) -> "DynamicLoadingPage":
        """
        Open dynamic loading example 1 or 2.
        Example 1: element hidden → becomes visible
        Example 2: element not in DOM → gets added
        """
        self.open(f"dynamic_loading/{example_number}")
        self.wait_for_clickable(self.START_BUTTON)
        log.info("Dynamic loading example %d opened", example_number)
        return self

    def click_start(self) -> "DynamicLoadingPage":
        """Click the Start button to trigger the loading animation."""
        log.info("Clicking Start button")
        self.click(self.START_BUTTON)
        return self

    def wait_for_loading_to_finish(self, timeout: int = 15) -> "DynamicLoadingPage":
        """
        Wait for the loading bar to disappear.

        CONCEPT: wait_for_invisible is the right tool here.
        The loading bar is visible while loading, invisible when done.
        We wait for it to become invisible before checking the result.
        """
        log.info("Waiting for loading bar to disappear...")
        self.wait_for_invisible(self.LOADING_BAR, timeout=timeout)
        return self

    def get_finish_text(self) -> str:
        """
        Get the text that appears after loading completes.

        CONCEPT: After the loading bar disappears, the #finish element
        either becomes visible (example 1) or is added to the DOM (example 2).
        We use wait_for_visible to handle both cases.
        """
        log.info("Reading finish text")
        return self.get_text(self.FINISH_TEXT)

    def start_and_wait(self, timeout: int = 15) -> str:
        """Convenience: click start, wait for finish, return result text."""
        self.click_start()
        self.wait_for_loading_to_finish(timeout)
        return self.get_finish_text()
