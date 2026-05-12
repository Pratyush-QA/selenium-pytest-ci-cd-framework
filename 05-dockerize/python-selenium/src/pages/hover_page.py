"""
src/pages/hover_page.py — Page Object for /hovers
==================================================
URL: https://the-internet.herokuapp.com/hovers
Demonstrates: ActionChains hover, revealing hidden elements
"""

from selenium.webdriver.common.by import By
from src.pages.base_page import BasePage
from src.utils.logger import get_logger

log = get_logger(__name__)


class HoverPage(BasePage):
    # ── Locators ──────────────────────────────────────────────────────────────
    # 3 avatar figures on the page
    FIGURES        = (By.CSS_SELECTOR, ".figure")
    # The caption that appears on hover (inside each figure)
    FIGURE_CAPTION = (By.CSS_SELECTOR, ".figure .figcaption h5")

    def open_hover_page(self) -> "HoverPage":
        self.open("hovers")
        self.wait_for_visible(self.FIGURES)
        log.info("Hover page opened")
        return self

    def hover_over_figure(self, index: int) -> "HoverPage":
        """
        Hover the mouse over the nth figure (0-indexed).

        CONCEPT: ActionChains.move_to_element() triggers the CSS :hover
        pseudo-class, making hidden elements with display:none or
        visibility:hidden become visible.
        """
        figures = self.driver.find_elements(*self.FIGURES)
        if index >= len(figures):
            raise IndexError(f"Figure index {index} out of range (only {len(figures)} figures)")
        log.info("Hovering over figure %d", index)
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(self.driver).move_to_element(figures[index]).perform()
        return self

    def get_caption_text(self, index: int) -> str:
        """Return the caption text revealed after hovering over figure at index."""
        captions = self.driver.find_elements(*self.FIGURE_CAPTION)
        return captions[index].text if index < len(captions) else ""

    def get_all_visible_captions(self) -> list[str]:
        """Return text of all currently visible captions."""
        return [el.text for el in self.driver.find_elements(*self.FIGURE_CAPTION)
                if el.is_displayed()]
