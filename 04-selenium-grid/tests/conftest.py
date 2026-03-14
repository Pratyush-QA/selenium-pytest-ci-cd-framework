"""
tests/conftest.py — ROOT conftest for the UI Selenium framework
================================================================
This is the most important file in the framework. It wires together:

  1. DRIVER FIXTURE       — creates/destroys WebDriver per test
  2. PAGE FIXTURES        — injects Page Objects into tests
  3. SCREENSHOT ON FAILURE — auto-captures screenshots when tests fail
  4. CLI OPTIONS          — --headless, --browser flags
  5. ALLURE ENVIRONMENT   — attaches browser/env info to reports
  6. SESSION HOOKS        — session-start/finish logging

FIXTURE SCOPES USED:
  function  → driver, all page objects (fresh browser per test = isolation)
  session   → settings info, logging (created once)

WHY function scope for the driver?
  Each test gets a completely fresh browser. No shared state, no cookies,
  no leftover form data from the previous test. This is slower but
  much more reliable than sharing a browser across tests.
"""

import pytest
import allure

from config.settings import settings
from src.driver.driver_factory import DriverFactory
from src.utils.helpers import screenshot_name
from src.utils.logger import get_logger

# Import all page classes for fixtures
from src.pages.login_page import LoginPage
from src.pages.dropdown_page import DropdownPage
from src.pages.checkbox_page import CheckboxPage
from src.pages.alert_page import AlertPage
from src.pages.iframe_page import IframePage
from src.pages.dynamic_loading_page import DynamicLoadingPage
from src.pages.hover_page import HoverPage
from src.pages.windows_page import WindowsPage

log = get_logger(__name__)


# =============================================================================
# CLI OPTION REGISTRATION
# =============================================================================
# CONCEPT: pytest_addoption lets you add custom flags to the pytest CLI.
# These become available in fixtures via request.config.getoption().
#
# Usage:
#   pytest --headless            → override config.ini headless=false
#   pytest --browser=firefox     → run on Firefox
#   pytest --env=staging         → load staging config section

def pytest_addoption(parser):
    """
    Register custom CLI options.
    Called once at the start of the session before collection.
    """
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (no visible window). Default: False",
    )
    parser.addoption(
        "--browser",
        action="store",
        default=None,
        choices=["chrome", "firefox"],
        help="Browser to use: chrome (default) or firefox",
    )
    parser.addoption(
        "--env",
        action="store",
        default=None,
        choices=["dev", "staging", "ci"],
        help="Environment to run against (overrides ENV env var)",
    )


# =============================================================================
# DRIVER FIXTURE
# =============================================================================

@pytest.fixture
def driver(request):
    """
    FUNCTION scope: Create a fresh WebDriver for EACH test, quit after.

    CONCEPT: The driver fixture is the heart of the UI framework.
      - Before the test (setup):  creates the browser
      - After the test (teardown): always quits the browser,
                                   even if the test failed

    CLI override examples:
      pytest --headless        → Chrome headless
      pytest --browser=firefox → Firefox headed

    The `request` object gives access to CLI options and test metadata.
    """
    # ── Determine browser settings ────────────────────────────────────────────
    headless = request.config.getoption("--headless") or settings.headless
    browser  = request.config.getoption("--browser") or settings.browser

    log.info(
        "🌐 [function] Creating %s driver | headless=%s | test=%s",
        browser, headless, request.node.name,
    )

    # ── Create the driver ────────────────────────────────────────────────────
    _driver = DriverFactory.create_driver(browser=browser, headless=headless)

    yield _driver

    # ── Teardown: always runs, even on test failure ───────────────────────────
    log.info("🔒 [function] Quitting driver | test=%s", request.node.name)
    _driver.quit()


# =============================================================================
# PAGE OBJECT FIXTURES
# =============================================================================
# CONCEPT: Instead of creating Page Objects inside every test, fixtures
# inject them. Tests just declare what they need as parameters.
#
# Usage in a test:
#   def test_login(login_page):
#       login_page.open_login_page().login("tomsmith", "SuperSecretPassword!")
#
# Each fixture passes the driver from the driver fixture automatically.

@pytest.fixture
def login_page(driver) -> LoginPage:
    """Inject a LoginPage instance backed by the test's driver."""
    return LoginPage(driver)


@pytest.fixture
def dropdown_page(driver) -> DropdownPage:
    return DropdownPage(driver)


@pytest.fixture
def checkbox_page(driver) -> CheckboxPage:
    return CheckboxPage(driver)


@pytest.fixture
def alert_page(driver) -> AlertPage:
    return AlertPage(driver)


@pytest.fixture
def iframe_page(driver) -> IframePage:
    return IframePage(driver)


@pytest.fixture
def dynamic_loading_page(driver) -> DynamicLoadingPage:
    return DynamicLoadingPage(driver)


@pytest.fixture
def hover_page(driver) -> HoverPage:
    return HoverPage(driver)


@pytest.fixture
def windows_page(driver) -> WindowsPage:
    return WindowsPage(driver)


# =============================================================================
# SCREENSHOT ON FAILURE HOOK
# =============================================================================
# CONCEPT: pytest_runtest_makereport + request.addfinalizer
# ──────────────────────────────────────────────────────────
# This is the standard pattern for capturing screenshots on test failure:
#
#   1. pytest_runtest_makereport is a hook called AFTER each test phase.
#   2. We store the report outcome on the `request` node.
#   3. The `take_screenshot_on_failure` fixture adds a finalizer that
#      checks: "did this test FAIL?" and if yes, takes a screenshot.
#
# The screenshot is:
#   a) Saved to screenshots/ folder with the test name + timestamp
#   b) Attached to the Allure report as a PNG attachment
#   c) Attached to the pytest-html report

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    HOOK: Intercept test results to store outcome on the item node.

    tryfirst=True  → run this before other hookwrappers
    hookwrapper=True → wrap around the actual test call

    We store the report so the screenshot fixture can read it.
    """
    outcome = yield
    report  = outcome.get_result()
    # Store the report for each phase: "setup", "call", "teardown"
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(autouse=True)
def take_screenshot_on_failure(request, driver):
    """
    AUTO-USE fixture: runs for every test automatically.
    After the test, checks if it failed and takes a screenshot if so.

    CONCEPT: autouse=True means this fixture applies to ALL tests in scope
    without needing to be listed as a parameter. It's invisible to tests.

    Why autouse is appropriate here:
      - Every UI test should auto-capture screenshots on failure
      - No test should need to explicitly opt in
      - The driver fixture is a dependency — runs only when driver is available
    """
    yield  # test runs here

    # ── Post-test: check if the test CALL phase failed ────────────────────────
    failed = getattr(request.node, "rep_call", None)
    if failed and failed.failed:
        test_name = request.node.name
        log.warning("📸 Test FAILED — capturing screenshot: %s", test_name)

        try:
            name    = screenshot_name(test_name)
            png     = driver.get_screenshot_as_png()
            png_path = settings.screenshot_dir / f"{name}.png"

            # ── Save to disk ───────────────────────────────────────────────────
            with open(png_path, "wb") as f:
                f.write(png)
            log.info("Screenshot saved: %s", png_path)

            # ── Attach to Allure report ────────────────────────────────────────
            # CONCEPT: allure.attach() embeds the PNG directly in the
            # Allure report so you can see EXACTLY what the browser showed
            # when the test failed — no need to look through files.
            allure.attach(
                png,
                name=f"FAILURE: {test_name}",
                attachment_type=allure.attachment_type.PNG,
            )

            # ── Attach to pytest-html report ──────────────────────────────────
            # pytest-html uses extras to embed images in the HTML report
            if hasattr(request.node, "extras"):
                from pytest_html import extras as html_extras
                request.node.extras.append(
                    html_extras.image(str(png_path), name="Screenshot on failure")
                )

        except Exception as exc:
            log.error("Failed to capture screenshot: %s", exc)


# =============================================================================
# SESSION HOOKS
# =============================================================================

def pytest_configure(config):
    """Attach environment information to the Allure report."""
    log.info(
        "🔧 UI Framework starting | env=%s | base_url=%s | browser=%s",
        settings.environment, settings.base_url, settings.browser,
    )


def pytest_sessionstart(session):
    log.info("🚀 UI test session started | env=%s", settings.environment)


def pytest_sessionfinish(session, exitstatus):
    status = {0: "✅ ALL PASSED", 1: "❌ SOME FAILED"}.get(exitstatus, f"code={exitstatus}")
    log.info("🏁 UI test session finished | result=%s", status)


def pytest_runtest_logreport(report):
    """Log pass/fail/skip for every test call."""
    if report.when == "call":
        if report.failed:
            log.error("❌ FAILED: %s (%.2fs)", report.nodeid, report.duration)
        elif report.passed:
            log.debug("✅ passed: %s (%.2fs)", report.nodeid, report.duration)
        elif report.skipped:
            log.warning("⏭  skipped: %s", report.nodeid)
