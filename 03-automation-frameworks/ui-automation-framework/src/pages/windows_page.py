"""
src/pages/windows_page.py — Page Object for /windows
=====================================================
URL: https://the-internet.herokuapp.com/windows
Demonstrates: opening new browser windows/tabs, switching between them
"""

from selenium.webdriver.common.by import By
from src.pages.base_page import BasePage
from src.utils.logger import get_logger

log = get_logger(__name__)


class WindowsPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    NEW_WINDOW_LINK  = (By.LINK_TEXT, "Click Here")
    NEW_WINDOW_TITLE = (By.CSS_SELECTOR, "h3")

    def open_windows_page(self) -> "WindowsPage":
        self.open("windows")
        self.wait_for_visible(self.NEW_WINDOW_LINK)
        log.info("Windows page opened")
        return self

    def click_new_window_link(self) -> "WindowsPage":
        """Click the link that opens a new browser window."""
        log.info("Clicking 'Click Here' to open new window")
        self.click(self.NEW_WINDOW_LINK)
        return self

    def switch_to_new_tab(self) -> "WindowsPage":
        """
        Switch driver focus to the newly opened window/tab.

        CONCEPT: After clicking a link that opens a new window:
          1. driver.window_handles grows from [main] to [main, new]
          2. We wait for 2 handles and switch to the last one

        The original window handle is always window_handles[0].
        """
        self.switch_to_new_window()
        log.info("Switched to new window. Current URL: %s", self.get_current_url())
        return self

    def get_new_window_heading(self) -> str:
        """Return the heading text on the new window page."""
        return self.get_text(self.NEW_WINDOW_TITLE)

    def close_new_window_and_return(self) -> "WindowsPage":
        """Close the current (new) window and switch back to the original."""
        self.close_current_window_and_switch_back()
        log.info("Closed new window, back to original")
        return self

    def get_window_count(self) -> int:
        """Return how many browser windows/tabs are currently open."""
        return len(self.driver.window_handles)
