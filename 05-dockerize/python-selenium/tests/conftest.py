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
from pytest_html import extras as html_extras

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
    parser.addoption(
        "--grid",
        action="store_true",
        default=False,
        help="Run tests on Selenium Grid (remote). Overrides config.ini use_grid.",
    )
    parser.addoption(
        "--grid-url",
        action="store",
        default=None,
        help="Selenium Grid hub URL (e.g. http://localhost:4444/wd/hub). Overrides config.ini grid_url.",
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
    use_grid = request.config.getoption("--grid") or settings.use_grid
    grid_url = request.config.getoption("--grid-url") or None  # None → settings default

    log.info(
        "🌐 [function] Creating %s driver | headless=%s | grid=%s | test=%s",
        browser, headless, use_grid, request.node.name,
    )

    # ── Create the driver ────────────────────────────────────────────────────
    _driver = DriverFactory.create_driver(
        browser=browser,
        headless=headless,
        use_grid=use_grid,
        grid_url=grid_url,
    )

    # CONCEPT: Store driver directly on the item node so hooks can access it.
    # Tests declare page object fixtures (login_page, checkbox_page etc),
    # NOT driver directly → item.funcargs.get("driver") returns None in hooks.
    # Storing on request.node makes the driver accessible via getattr(item, "_driver")
    # in pytest_runtest_makereport, regardless of what the test declares.
    request.node._driver = _driver

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
    HOOK: Store test outcome AND capture screenshot base64 on the item node.

    tryfirst=True    → run this before other hookwrappers
    hookwrapper=True → wrap around the actual test call

    CONCEPT: WHY we only CAPTURE here, not attach to HTML:
    ───────────────────────────────────────────────────────
    pytest-html v4 manages extras through its own `extra` fixture + stash.
    Setting report.extras directly here gets OVERWRITTEN by pytest-html's
    internal `extra` fixture teardown which runs after this hook.

    So we split the job into 2 steps:
      Step 1 (HERE)   → capture screenshot base64 while driver is still alive
                        store it on item._failure_screenshot
      Step 2 (fixture) → attach_screenshot_to_html fixture reads it after test
                         appends to `extra` fixture (pytest-html v4 proper API)
                         `extra` fixture teardown then writes to report.extras ✅

    Timeline:
      call phase → hook fires → item._failure_screenshot = base64  ← HERE
      teardown   → attach_screenshot_to_html → extra.append(image)
                → extra fixture teardown    → report.extras.extend(list)
                → driver.quit()
    """
    outcome = yield
    report  = outcome.get_result()

    # ── Store phase result on item for fixture teardown checks ────────────────
    setattr(item, f"rep_{report.when}", report)

    # ── Capture screenshot base64 while driver is still alive ─────────────────
    # Only capture during "call" phase (actual test body), not setup/teardown.
    # item._driver is set by the driver fixture — always available regardless
    # of whether the test function directly requests driver or login_page etc.
    if report.when == "call" and report.failed:
        driver = getattr(item, "_driver", None)
        if driver:
            try:
                item._failure_screenshot = driver.get_screenshot_as_base64()
                log.warning("📸 Screenshot captured for report: %s", item.name)
            except Exception as exc:
                log.error("Failed to capture screenshot: %s", exc)


@pytest.fixture(autouse=True)
def attach_screenshot_to_html(request, extra):
    """
    AUTO-USE fixture: attaches failure screenshot to pytest-html v4 report.

    CONCEPT: pytest-html v4 extras API
    ────────────────────────────────────
    In pytest-html v4, the ONLY reliable way to embed extras in the HTML
    report is through the `extra` fixture it provides. This fixture:
      1. Yields a list you append to
      2. In its OWN teardown, writes that list into report.extras
      3. pytest-html reads report.extras when generating the final HTML

    We DON'T set report.extras directly because pytest-html v4 overwrites it
    via the `extra` fixture stash mechanism. Instead:
      - The hook captures screenshot → stores on item._failure_screenshot
      - This fixture reads it after test → appends to `extra` list
      - `extra` fixture teardown runs AFTER this fixture teardown
        (dependency order: this depends on extra → extra tears down last)
        and writes our screenshot into report.extras ✅

    WHY separate from take_screenshot_on_failure:
      take_screenshot_on_failure depends on `driver` — for disk/Allure
      attach_screenshot_to_html  depends on `extra`  — for HTML report
      Keeping them separate ensures clean dependency chains.
    """
    yield  # test runs here

    # ── Read screenshot stored by hook, attach to HTML report ─────────────────
    screenshot = getattr(request.node, "_failure_screenshot", None)
    if screenshot:
        extra.append(
            html_extras.image(
                screenshot,
                mime_type="image/png",
                name=f"FAILURE: {request.node.name}",
            )
        )
        log.info("📎 Screenshot attached to HTML report: %s", request.node.name)


@pytest.fixture(autouse=True)
def take_screenshot_on_failure(request, driver):
    """
    AUTO-USE fixture: saves screenshot to disk + attaches to Allure on failure.

    CONCEPT: autouse=True means this fixture applies to ALL tests in scope
    without needing to be listed as a parameter. It's invisible to tests.

    Responsibilities clearly split:
    ────────────────────────────────
    pytest_runtest_makereport hook  → captures base64,  stores on item node
    attach_screenshot_to_html       → reads base64,     attaches to HTML report
    take_screenshot_on_failure      → captures PNG,     saves to disk + Allure
    """
    yield  # test runs here

    # ── Post-test: check if the test CALL phase failed ────────────────────────
    failed = getattr(request.node, "rep_call", None)
    if failed and failed.failed:
        test_name = request.node.name
        log.warning("📸 Test FAILED — saving screenshot to disk: %s", test_name)

        try:
            name     = screenshot_name(test_name)
            png      = driver.get_screenshot_as_png()
            png_path = settings.screenshot_dir / f"{name}.png"

            # ── Save to disk ───────────────────────────────────────────────────
            with open(png_path, "wb") as f:
                f.write(png)
            log.info("Screenshot saved to disk: %s", png_path)

            # ── Attach to Allure report ────────────────────────────────────────
            # CONCEPT: allure.attach() embeds the PNG directly in the
            # Allure report so you can see EXACTLY what the browser showed
            # when the test failed — no need to look through files.
            allure.attach(
                png,
                name=f"FAILURE: {test_name}",
                attachment_type=allure.attachment_type.PNG,
            )

        except Exception as exc:
            log.error("Failed to save screenshot: %s", exc)


# =============================================================================
# SESSION HOOKS
# =============================================================================

def pytest_configure(config):
    """Attach environment information to the Allure report."""
    # Ensure reports/ folder exists before pytest-html tries to write the report
    from pathlib import Path
    Path("reports").mkdir(exist_ok=True)

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
