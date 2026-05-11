"""
src/driver/driver_factory.py — WebDriver factory
=================================================
CONCEPT: Driver Factory Pattern
────────────────────────────────
The factory pattern centralises all browser/driver configuration in one place.
Tests never call selenium directly — they just ask the factory for a driver.

This means:
  ✔ Switch browsers by changing ONE setting (config.ini browser = firefox)
  ✔ Toggle headless with an env var (HEADLESS=true)
  ✔ Two driver setup strategies in the same file:
      1. Selenium Manager  → Selenium 4.6+ built-in, zero install
      2. webdriver-manager → explicit pip package, older Selenium compat

CONCEPT: Selenium Manager vs webdriver-manager
───────────────────────────────────────────────
┌──────────────────────┬──────────────────────────────────────────────────┐
│ Selenium Manager     │ webdriver-manager                                │
├──────────────────────┼──────────────────────────────────────────────────┤
│ Built into Selenium  │ Separate pip package (webdriver-manager)         │
│ 4.6+ (2022)          │                                                  │
│ Zero config — just   │ Explicit: ChromeDriverManager().install()        │
│ create WebDriver()   │                                                  │
│ Downloads & caches   │ Downloads to ~/.wdm/ cache folder                │
│ driver automatically │                                                  │
│ No imports needed    │ from webdriver_manager.chrome import ...         │
│ Recommended default  │ Useful if you need a specific driver version     │
└──────────────────────┴──────────────────────────────────────────────────┘

Switch mode in config.ini:
  driver_mode = selenium_manager     ← default, recommended
  driver_mode = webdriver_manager    ← explicit manager

Usage in tests (via fixture — you never call this directly):
    # In conftest.py:
    driver = DriverFactory.create_driver()
    yield driver
    driver.quit()
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

from config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


def _build_chrome_options(headless: bool) -> ChromeOptions:
    """
    Build ChromeOptions with production-grade settings for CI/CD stability.

    CONCEPT: Chrome flags explained:
      --headless=new           → New headless mode (Selenium 4.x). Renders
                                 pages properly unlike the old --headless flag.
      --no-sandbox             → Required inside Docker (root user restriction).
      --disable-dev-shm-usage  → Prevents crashes in Docker due to small /dev/shm.
      --disable-gpu            → Disables GPU in headless (no display available).
      --window-size            → Sets viewport; headless has no default window.
      --disable-extensions     → Faster startup, no extension interference.
      --disable-notifications  → Prevents notification popups breaking tests.
      --remote-debugging-port  → Enables DevTools Protocol (useful for debugging).
    """
    options = ChromeOptions()

    if headless:
        options.add_argument("--headless=new")      # newer, more reliable headless
        options.add_argument("--no-sandbox")         # REQUIRED in Docker
        options.add_argument("--disable-dev-shm-usage")  # REQUIRED in Docker
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
    else:
        # Headed mode — still useful to standardise the window size
        options.add_argument("--start-maximized")

    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--remote-debugging-port=9222")

    # Suppress "Chrome is being controlled by automated test software" banner
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    log.debug("ChromeOptions built | headless=%s", headless)
    return options


def _build_firefox_options(headless: bool) -> FirefoxOptions:
    """Build FirefoxOptions for headed or headless Firefox."""
    options = FirefoxOptions()
    if headless:
        options.add_argument("--headless")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
    log.debug("FirefoxOptions built | headless=%s", headless)
    return options


class DriverFactory:
    """
    Factory class that creates configured WebDriver instances.

    CONCEPT: Why a factory class?
      - All creation logic lives here, tests stay clean
      - Easy to add new browsers (Edge, Safari) without changing tests
      - Easy to switch driver strategy (Selenium Manager vs webdriver-manager)
    """

    @staticmethod
    def create_driver(
        browser: str = None,
        headless: bool = None,
        driver_mode: str = None,
    ) -> webdriver.Remote:
        """
        Create and return a configured WebDriver instance.

        Args:
            browser:     "chrome" | "firefox" (defaults to config.ini value)
            headless:    True/False (defaults to config.ini value)
            driver_mode: "selenium_manager" | "webdriver_manager"

        Returns:
            A ready-to-use WebDriver instance with timeouts configured.
        """
        # Use settings as defaults, allow override per-call
        browser     = (browser     or settings.browser    ).lower()
        headless    = headless     if headless is not None else settings.headless
        driver_mode = driver_mode  or settings.driver_mode

        log.info(
            "Creating WebDriver | browser=%s | headless=%s | mode=%s",
            browser, headless, driver_mode,
        )

        if browser == "chrome":
            driver = DriverFactory._create_chrome(headless, driver_mode)
        elif browser == "firefox":
            driver = DriverFactory._create_firefox(headless, driver_mode)
        else:
            raise ValueError(
                f"Unsupported browser: '{browser}'. Choose 'chrome' or 'firefox'."
            )

        # ── Configure global timeouts ─────────────────────────────────────────
        # CONCEPT: page_load_timeout vs implicit_wait vs explicit_wait
        #
        # page_load_timeout → max seconds to wait for a full page load after
        #                     driver.get(url). Raises TimeoutException if exceeded.
        #
        # implicit_wait     → how long Selenium waits when find_element() can't
        #                     find an element immediately. Set to 0 here because
        #                     mixing implicit + explicit waits causes weird bugs.
        #                     We use ONLY explicit waits (WebDriverWait).
        #
        # script_timeout    → max seconds for execute_script() / execute_async_script()
        driver.set_page_load_timeout(settings.page_load_timeout)
        driver.implicitly_wait(settings.implicit_wait)  # 0 = disabled

        log.info("WebDriver created successfully")
        return driver

    # ── Chrome ────────────────────────────────────────────────────────────────

    @staticmethod
    def _create_chrome(headless: bool, driver_mode: str):
        options = _build_chrome_options(headless)

        if driver_mode == "webdriver_manager":
            # ── Strategy 1: webdriver-manager (pip install webdriver-manager) ──
            # CONCEPT: webdriver-manager downloads the exact ChromeDriver binary
            # that matches your installed Chrome version and caches it in ~/.wdm/
            # Great for teams that need a specific driver version pinned.
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = ChromeService(ChromeDriverManager().install())
                log.info("Chrome via webdriver-manager | driver=%s", service.path)
                return webdriver.Chrome(service=service, options=options)
            except ImportError:
                log.warning(
                    "webdriver-manager not installed. "
                    "Falling back to Selenium Manager. "
                    "Run: pip install webdriver-manager"
                )
                # Fall through to Selenium Manager below

        # ── Strategy 2: Selenium Manager (Selenium 4.6+, built-in, default) ──
        # CONCEPT: Since Selenium 4.6, the framework ships with its own
        # "Selenium Manager" that auto-downloads the correct ChromeDriver.
        # You don't import or configure anything — just create webdriver.Chrome().
        log.info("Chrome via Selenium Manager (built-in)")
        return webdriver.Chrome(options=options)

    # ── Firefox ───────────────────────────────────────────────────────────────

    @staticmethod
    def _create_firefox(headless: bool, driver_mode: str):
        options = _build_firefox_options(headless)

        if driver_mode == "webdriver_manager":
            try:
                from webdriver_manager.firefox import GeckoDriverManager
                service = FirefoxService(GeckoDriverManager().install())
                log.info("Firefox via webdriver-manager | driver=%s", service.path)
                return webdriver.Firefox(service=service, options=options)
            except ImportError:
                log.warning("webdriver-manager not installed. Falling back to Selenium Manager.")

        log.info("Firefox via Selenium Manager (built-in)")
        return webdriver.Firefox(options=options)
