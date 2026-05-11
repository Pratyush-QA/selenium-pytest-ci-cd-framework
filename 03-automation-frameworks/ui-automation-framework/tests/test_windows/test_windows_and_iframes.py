"""
tests/test_windows/test_windows_and_iframes.py — Multi-window and iFrame tests
================================================================================
CONCEPTS DEMONSTRATED:
  ✔ driver.window_handles — switching between browser tabs
  ✔ switch_to_frame() / switch_to_default() — iFrame context switching
  ✔ EC.number_of_windows_to_be() — wait for new tab to open
"""

import pytest
import allure

from src.pages.windows_page import WindowsPage
from src.pages.iframe_page import IframePage
from src.utils.logger import get_logger

log = get_logger(__name__)


# =============================================================================
# MULTI-WINDOW TESTS
# =============================================================================

@allure.feature("Windows")
@allure.story("New Window Opens")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.smoke
@pytest.mark.windows
def test_new_window_opens_on_click(windows_page: WindowsPage):
    """
    Click a link, verify a new window opens, check its content.

    CONCEPT: Window handle flow:
      1. Start: window_handles = [main_handle]
      2. Click link: window_handles = [main_handle, new_handle]
      3. switch_to.window(new_handle): driver now controls new tab
      4. Interact with new tab
      5. Close new tab + switch back to main
    """
    with allure.step("Open the windows page"):
        windows_page.open_windows_page()

    with allure.step("Assert only 1 window before clicking"):
        assert windows_page.get_window_count() == 1

    with allure.step("Click link to open new window"):
        windows_page.click_new_window_link()

    with allure.step("Switch to the new window"):
        windows_page.switch_to_new_tab()

    with allure.step("Assert new window URL contains 'new'"):
        current_url = windows_page.get_current_url()
        allure.attach(current_url, "New Window URL", allure.attachment_type.TEXT)
        assert "new" in current_url

    with allure.step("Assert 2 windows are open"):
        assert windows_page.get_window_count() == 2

    with allure.step("Close new window and switch back"):
        windows_page.close_new_window_and_return()
        assert windows_page.get_window_count() == 1


@allure.feature("Windows")
@allure.story("New Window Content")
@pytest.mark.regression
@pytest.mark.windows
def test_new_window_has_correct_heading(windows_page: WindowsPage):
    """Verify the heading text on the newly opened window."""
    windows_page.open_windows_page()
    windows_page.click_new_window_link()
    windows_page.switch_to_new_tab()

    heading = windows_page.get_new_window_heading()
    allure.attach(heading, "New Window Heading", allure.attachment_type.TEXT)
    assert "New Window" in heading, f"Unexpected heading: '{heading}'"

    windows_page.close_new_window_and_return()


# =============================================================================
# IFRAME TESTS
# =============================================================================

@allure.feature("iFrames")
@allure.story("Read Content Inside iFrame")
@allure.severity(allure.severity_level.NORMAL)
@pytest.mark.smoke
@pytest.mark.windows
def test_read_text_inside_iframe(iframe_page: IframePage):
    """
    Read text from inside a TinyMCE iframe editor.

    CONCEPT: iFrame context switching:
      ├── Main page context (default)
      │   └── driver can interact with main page elements
      │
      └── After switch_to_frame(iframe):
          └── driver can ONLY interact with elements inside the iframe
              (elements outside are NOT accessible until switch_to_default)
    """
    with allure.step("Open iframe page"):
        iframe_page.open_iframe_page()

    with allure.step("Read editor text from inside iframe"):
        text = iframe_page.get_editor_text()
        allure.attach(text, "Editor Text Inside iFrame", allure.attachment_type.TEXT)

    with allure.step("Assert editor contains default text"):
        assert text, "Editor text should not be empty"
        # TinyMCE editor default content
        assert len(text) > 0


@allure.feature("iFrames")
@allure.story("Type Inside iFrame")
@pytest.mark.regression
@pytest.mark.windows
@pytest.mark.parametrize("new_text", [
    "Hello from Pytest UI Framework!",
    "Selenium + POM = Clean Tests",
])
def test_type_inside_iframe(iframe_page: IframePage, new_text: str):
    """
    Clear editor and type new content inside the iframe.
    Verify the text is saved correctly.
    """
    with allure.step("Open iframe page"):
        iframe_page.open_iframe_page()

    with allure.step(f"Type '{new_text}' into the iframe editor"):
        iframe_page.clear_and_type_in_editor(new_text)

    with allure.step("Read back and verify the text"):
        result = iframe_page.get_editor_text()
        assert new_text in result, f"Expected '{new_text}' in editor, got '{result}'"
