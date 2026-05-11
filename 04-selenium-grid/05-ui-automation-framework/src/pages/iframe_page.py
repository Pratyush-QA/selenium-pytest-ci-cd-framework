"""
src/pages/iframe_page.py — Page Object for /iframe
===================================================
URL: https://the-internet.herokuapp.com/iframe
Demonstrates: switching driver context into/out of iFrames
"""

from selenium.webdriver.common.by import By
from src.pages.base_page import BasePage
from src.utils.logger import get_logger

log = get_logger(__name__)


class IframePage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    # The iframe itself — identified by its ID
    IFRAME         = (By.ID, "mce_0_ifr")
    # The editable body inside the iframe
    EDITOR_BODY    = (By.ID, "tinymce")
    # Bold button in the TinyMCE toolbar (outside the iframe)
    BOLD_BUTTON    = (By.CSS_SELECTOR, "button[data-mce-name='bold']")

    def open_iframe_page(self) -> "IframePage":
        self.open("iframe")
        # Wait for the iframe element to be present in the DOM
        self.wait_for_present(self.IFRAME)
        log.info("Iframe page opened")
        return self

    def get_editor_text(self) -> str:
        """
        Read text from inside the TinyMCE iframe editor.

        CONCEPT: Steps for working with iFrames:
          1. switch_to_frame()       → enter the iframe context
          2. interact with elements inside
          3. switch_to_default()     → return to main page context

        If you forget step 3, all subsequent interactions will fail
        because the driver is still looking inside the iframe.
        """
        log.info("Reading text from inside iframe")
        self.switch_to_frame(self.IFRAME)
        text = self.get_text(self.EDITOR_BODY)
        self.switch_to_default()
        return text

    def clear_and_type_in_editor(self, text: str) -> "IframePage":
        """Clear the editor content and type new text inside the iframe."""
        log.info("Typing '%s' into iframe editor", text)
        self.switch_to_frame(self.IFRAME)
        body = self.wait_for_visible(self.EDITOR_BODY)
        body.clear()
        body.send_keys(text)
        self.switch_to_default()
        return self
