"""
src/pages/base_page.py — BasePage: foundation of the Page Object Model
=======================================================================
CONCEPT: Page Object Model (POM)
──────────────────────────────────
POM is the most important design pattern in UI test automation.

PROBLEM without POM:
    # Test file has raw Selenium code scattered everywhere:
    driver.find_element(By.ID, "username").send_keys("tomsmith")
    driver.find_element(By.ID, "password").send_keys("SuperSecretPassword!")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    # If the login button's selector changes → update EVERY test file manually

SOLUTION with POM:
    # Test file is clean and readable:
    login_page.enter_username("tomsmith")
    login_page.enter_password("SuperSecretPassword!")
    login_page.click_login()
    # If selector changes → update ONLY LoginPage. All tests auto-fixed.

STRUCTURE:
    BasePage          ← shared actions (click, type, wait, scroll, etc.)
        ↑
    LoginPage         ← login-specific elements and actions
    DropdownPage      ← dropdown-specific elements and actions
    CheckboxPage      ← etc.

This BasePage class provides:
  ✔ Explicit wait wrappers (wait_for_element, wait_for_text, etc.)
  ✔ Safe click / type / select helpers
  ✔ Scroll utilities
  ✔ Screenshot capture
  ✔ JavaScript execution helpers
  ✔ ActionChains wrappers (hover, right-click, drag-drop)
"""

import time
from pathlib import Path
from typing import Optional

import allure
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
    StaleElementReferenceException,
)

from config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


class BasePage:
    """
    Base class for all Page Objects.

    Every page class inherits from this. It stores the driver reference
    and provides reusable low-level browser interaction methods so that
    individual page classes only define WHAT is on the page, not HOW
    to interact with the browser.

    Constructor Args:
        driver: The active WebDriver instance (injected via fixture).
    """

    def __init__(self, driver: WebDriver):
        self.driver  = driver
        self.wait    = WebDriverWait(
            driver,
            timeout=settings.explicit_wait,
            ignored_exceptions=[StaleElementReferenceException],
        )
        self.actions = ActionChains(driver)

    # ── Navigation ────────────────────────────────────────────────────────────

    def open(self, path: str = "") -> "BasePage":
        """
        Navigate to base_url + path.

        CONCEPT: Calling open() on a page object navigates to its URL.
        This is cleaner than calling driver.get() in every test.

        Usage:
            login_page.open()         → opens /login
            home_page.open("/about")  → opens /about
        """
        url = f"{settings.base_url}/{path.lstrip('/')}"
        log.info("Navigating to %s", url)
        self.driver.get(url)
        return self

    def get_title(self) -> str:
        return self.driver.title

    def get_current_url(self) -> str:
        return self.driver.current_url

    def go_back(self):
        self.driver.back()

    def refresh(self):
        self.driver.refresh()

    # ── Explicit Wait Helpers ─────────────────────────────────────────────────
    #
    # CONCEPT: Explicit Waits vs Implicit Waits
    # ───────────────────────────────────────────
    # NEVER mix the two — it causes unpredictable timeouts.
    # We set implicit_wait=0 in the factory and use ONLY explicit waits.
    #
    # WebDriverWait(driver, timeout).until(expected_condition)
    #
    # Common expected_conditions (EC):
    #   EC.presence_of_element_located(locator)   → element exists in DOM
    #   EC.visibility_of_element_located(locator) → element is visible
    #   EC.element_to_be_clickable(locator)        → visible + enabled
    #   EC.text_to_be_present_in_element(locator, text)
    #   EC.invisibility_of_element_located(locator)
    #   EC.staleness_of(element)
    #   EC.alert_is_present()
    #   EC.frame_to_be_available_and_switch_to_it(locator)
    #   EC.number_of_windows_to_be(n)

    def wait_for_visible(self, locator: tuple, timeout: int = None) -> WebElement:
        """Wait until element is visible, return it."""
        t = timeout or settings.explicit_wait
        log.debug("Waiting for visible: %s (timeout=%ds)", locator, t)
        return WebDriverWait(self.driver, t).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_for_clickable(self, locator: tuple, timeout: int = None) -> WebElement:
        """Wait until element is visible AND enabled (ready to click)."""
        t = timeout or settings.explicit_wait
        return WebDriverWait(self.driver, t).until(
            EC.element_to_be_clickable(locator)
        )

    def wait_for_present(self, locator: tuple, timeout: int = None) -> WebElement:
        """Wait until element exists in DOM (may be invisible)."""
        t = timeout or settings.explicit_wait
        return WebDriverWait(self.driver, t).until(
            EC.presence_of_element_located(locator)
        )

    def wait_for_text(self, locator: tuple, text: str, timeout: int = None) -> bool:
        """Wait until element contains specific text."""
        t = timeout or settings.explicit_wait
        return WebDriverWait(self.driver, t).until(
            EC.text_to_be_present_in_element(locator, text)
        )

    def wait_for_invisible(self, locator: tuple, timeout: int = None) -> bool:
        """Wait until element is no longer visible (e.g. loading spinner gone)."""
        t = timeout or settings.explicit_wait
        return WebDriverWait(self.driver, t).until(
            EC.invisibility_of_element_located(locator)
        )

    def wait_for_url_contains(self, text: str, timeout: int = None) -> bool:
        """Wait until current URL contains a given string."""
        t = timeout or settings.explicit_wait
        return WebDriverWait(self.driver, t).until(EC.url_contains(text))

    def wait_for_alert(self, timeout: int = None):
        """Wait for a JavaScript alert/confirm/prompt and return the Alert object."""
        t = timeout or settings.explicit_wait
        return WebDriverWait(self.driver, t).until(EC.alert_is_present())

    def is_element_visible(self, locator: tuple, timeout: int = 3) -> bool:
        """Return True if element is visible within timeout, False otherwise."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    # ── Click / Type ──────────────────────────────────────────────────────────

    def click(self, locator: tuple) -> None:
        """Wait for element to be clickable, then click it."""
        element = self.wait_for_clickable(locator)
        log.debug("Clicking: %s", locator)
        element.click()

    def type_text(self, locator: tuple, text: str, clear_first: bool = True) -> None:
        """
        Wait for element, optionally clear it, then type text.

        CONCEPT: Always clear before typing in tests — leftover text
        from a previous test or page state causes hard-to-debug failures.
        """
        element = self.wait_for_visible(locator)
        if clear_first:
            element.clear()
        log.debug("Typing '%s' into: %s", text, locator)
        element.send_keys(text)

    def get_text(self, locator: tuple) -> str:
        """Return the visible text of an element."""
        element = self.wait_for_visible(locator)
        return element.text.strip()

    def get_attribute(self, locator: tuple, attribute: str) -> str:
        """Return the value of an HTML attribute on an element."""
        element = self.wait_for_present(locator)
        return element.get_attribute(attribute)

    def press_key(self, locator: tuple, key) -> None:
        """Send a keyboard key to an element (e.g. Keys.RETURN, Keys.TAB)."""
        element = self.wait_for_visible(locator)
        element.send_keys(key)

    # ── Select / Dropdown ──────────────────────────────────────────────────────

    def select_by_visible_text(self, locator: tuple, text: str) -> None:
        """
        Select a <select> dropdown option by its visible text.

        CONCEPT: Selenium's Select class wraps <select> elements.
        Three ways to select:
          select.select_by_visible_text("Option 1")  → by label
          select.select_by_value("val1")              → by value attribute
          select.select_by_index(0)                   → by position
        """
        element = self.wait_for_visible(locator)
        Select(element).select_by_visible_text(text)
        log.debug("Selected '%s' from dropdown: %s", text, locator)

    def select_by_value(self, locator: tuple, value: str) -> None:
        element = self.wait_for_visible(locator)
        Select(element).select_by_value(value)

    def get_selected_option_text(self, locator: tuple) -> str:
        element = self.wait_for_visible(locator)
        return Select(element).first_selected_option.text

    def get_all_dropdown_options(self, locator: tuple) -> list[str]:
        element = self.wait_for_visible(locator)
        return [opt.text for opt in Select(element).options]

    # ── Checkbox / Radio ──────────────────────────────────────────────────────

    def is_checked(self, locator: tuple) -> bool:
        element = self.wait_for_present(locator)
        return element.is_selected()

    def check(self, locator: tuple) -> None:
        """Check a checkbox only if it's not already checked."""
        if not self.is_checked(locator):
            self.click(locator)

    def uncheck(self, locator: tuple) -> None:
        """Uncheck a checkbox only if it's currently checked."""
        if self.is_checked(locator):
            self.click(locator)

    # ── Alerts ────────────────────────────────────────────────────────────────

    def accept_alert(self) -> str:
        """
        Wait for an alert, capture its text, then accept (click OK).

        CONCEPT: JavaScript alert types:
          alert("msg")          → alert    → only OK button
          confirm("msg")        → confirm  → OK or Cancel
          prompt("msg","default") → prompt → text input + OK/Cancel
        """
        alert = self.wait_for_alert()
        text  = alert.text
        log.debug("Accepting alert: '%s'", text)
        alert.accept()
        return text

    def dismiss_alert(self) -> str:
        """Wait for a confirm/prompt alert and click Cancel."""
        alert = self.wait_for_alert()
        text  = alert.text
        log.debug("Dismissing alert: '%s'", text)
        alert.dismiss()
        return text

    def type_in_prompt(self, text: str) -> str:
        """Type text into a JavaScript prompt then accept it."""
        alert = self.wait_for_alert()
        alert_text = alert.text
        alert.send_keys(text)
        alert.accept()
        return alert_text

    # ── iFrames ───────────────────────────────────────────────────────────────

    def switch_to_frame(self, locator: tuple) -> None:
        """
        Switch driver context into an iframe.

        CONCEPT: Selenium can't interact with elements inside an <iframe>
        until you switch the driver context into it. Always switch back
        out when done using switch_to_default_content().
        """
        log.debug("Switching to frame: %s", locator)
        self.wait.until(EC.frame_to_be_available_and_switch_to_it(locator))

    def switch_to_default(self) -> None:
        """Switch back to the main page from any frame."""
        self.driver.switch_to.default_content()

    # ── Windows / Tabs ────────────────────────────────────────────────────────

    def switch_to_new_window(self) -> None:
        """
        Switch to the most recently opened browser window/tab.

        CONCEPT: driver.window_handles is a list of window handles.
        After a link opens a new tab, the new handle appears at [-1].
        """
        self.wait.until(EC.number_of_windows_to_be(2))
        new_handle = self.driver.window_handles[-1]
        log.debug("Switching to new window: %s", new_handle)
        self.driver.switch_to.window(new_handle)

    def switch_to_window(self, index: int = 0) -> None:
        """Switch to a specific window by index (0=original, 1=first new, etc.)."""
        handle = self.driver.window_handles[index]
        self.driver.switch_to.window(handle)

    def close_current_window_and_switch_back(self) -> None:
        """Close current window/tab and switch back to the original."""
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

    # ── ActionChains ──────────────────────────────────────────────────────────
    #
    # CONCEPT: ActionChains
    # ─────────────────────
    # ActionChains lets you build a sequence of low-level mouse/keyboard
    # actions and execute them all at once with .perform().
    #
    # Common actions:
    #   .move_to_element(element)   → hover
    #   .click(element)             → left click
    #   .double_click(element)      → double click
    #   .context_click(element)     → right click
    #   .click_and_hold(element)    → mouse down
    #   .release(target)            → mouse up
    #   .drag_and_drop(src, target) → drag from src to target
    #   .send_keys(Keys.RETURN)     → keyboard input

    def hover(self, locator: tuple) -> None:
        """Hover the mouse over an element (triggers CSS :hover state)."""
        element = self.wait_for_visible(locator)
        log.debug("Hovering over: %s", locator)
        ActionChains(self.driver).move_to_element(element).perform()

    def double_click(self, locator: tuple) -> None:
        """Double-click an element."""
        element = self.wait_for_clickable(locator)
        ActionChains(self.driver).double_click(element).perform()

    def right_click(self, locator: tuple) -> None:
        """Right-click (context menu) an element."""
        element = self.wait_for_clickable(locator)
        ActionChains(self.driver).context_click(element).perform()

    def drag_and_drop(self, source_locator: tuple, target_locator: tuple) -> None:
        """
        Drag element from source to target.

        CONCEPT: drag_and_drop uses:
          1. click_and_hold on source
          2. move_to_element to target
          3. release
        """
        source = self.wait_for_visible(source_locator)
        target = self.wait_for_visible(target_locator)
        log.debug("Drag from %s → %s", source_locator, target_locator)
        ActionChains(self.driver).drag_and_drop(source, target).perform()

    # ── Scroll ────────────────────────────────────────────────────────────────

    def scroll_to_element(self, locator: tuple) -> None:
        """Scroll element into the visible viewport using JavaScript."""
        element = self.wait_for_present(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the page."""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    def scroll_to_top(self) -> None:
        """Scroll back to the top of the page."""
        self.driver.execute_script("window.scrollTo(0, 0);")

    # ── JavaScript Execution ──────────────────────────────────────────────────

    def js_click(self, locator: tuple) -> None:
        """
        Click via JavaScript — bypass normal click issues.

        Use when:
          - Element is covered by another element (overlapping)
          - Element is not visible in the viewport
          - Regular .click() throws ElementNotInteractableException
        """
        element = self.wait_for_present(locator)
        self.driver.execute_script("arguments[0].click();", element)

    def js_set_value(self, locator: tuple, value: str) -> None:
        """Set an input's value using JavaScript (bypasses readonly attribute)."""
        element = self.wait_for_present(locator)
        self.driver.execute_script(f"arguments[0].value = '{value}';", element)

    def get_js_value(self, script: str) -> object:
        """Execute arbitrary JavaScript and return its result."""
        return self.driver.execute_script(script)

    # ── Screenshot ────────────────────────────────────────────────────────────

    def take_screenshot(self, name: str = "screenshot") -> bytes:
        """
        Capture a screenshot of the current browser window.

        Returns the raw PNG bytes (used by conftest.py for Allure attachment
        and for saving to the screenshots/ folder on failure).
        """
        png = self.driver.get_screenshot_as_png()
        log.debug("Screenshot taken: %s", name)
        return png

    def save_screenshot(self, name: str = "screenshot") -> Path:
        """Save screenshot to the configured screenshots/ directory."""
        path = settings.screenshot_dir / f"{name}.png"
        self.driver.save_screenshot(str(path))
        log.info("Screenshot saved: %s", path)
        return path
