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

import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

from config.settings import settings
from src.utils.logger import get_logger

log = get_logger(__name__)


def _is_running_in_container() -> bool:
    """Return True when the framework is running inside a Docker container."""
    return os.path.exists("/.dockerenv") or os.getenv("ENV", "").lower() == "ci"


def _build_chrome_options(headless: bool, is_remote: bool = False) -> ChromeOptions:
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

    CONCEPT: is_remote=True (Grid) vs is_remote=False (local):
      --remote-debugging-port  → LOCAL ONLY. On Grid (SE_NODE_MAX_SESSIONS > 1),
                                 multiple Chrome sessions share the same container.
                                 Each tries to bind port 9222 → port conflict →
                                 session fails. Never pass this flag to Grid.
      --no-sandbox             → ALWAYS required inside Docker containers,
                                 regardless of headless mode.
      --disable-dev-shm-usage  → ALWAYS required in Docker (small /dev/shm).
      excludeSwitches /        → LOCAL ONLY. Experimental options can cause
      useAutomationExtension     instability on remote Grid sessions.
    """
    options = ChromeOptions()

    if headless:
        options.add_argument("--headless=new")      # newer, more reliable headless
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
    else:
        options.add_argument("--start-maximized")

    # Docker-required flags: needed for both standalone Docker and Grid nodes.
    is_container = _is_running_in_container()

    if is_remote or is_container:
        # Required in Docker because containers often run as root with small /dev/shm.
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")  # small /dev/shm in Docker

    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    if not is_remote and not is_container:
        # LOCAL ONLY: --remote-debugging-port binds a fixed port (9222).
        # On Grid with SE_NODE_MAX_SESSIONS > 1, all sessions run on the same
        # container → multiple Chrome instances fight for port 9222 → 1 fails.
        # In standalone Docker parallel runs, multiple local Chrome instances
        # can hit the same issue, so avoid this flag inside containers too.
        options.add_argument("--remote-debugging-port=9222")

        # LOCAL ONLY: experimental options can cause instability on remote sessions
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

    log.debug("ChromeOptions built | headless=%s | is_remote=%s", headless, is_remote)
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
        use_grid: bool = None,
        grid_url: str = None,
    ) -> webdriver.Remote:
        """
        Create and return a configured WebDriver instance.

        Args:
            browser:     "chrome" | "firefox" (defaults to config.ini value)
            headless:    True/False (defaults to config.ini value)
            driver_mode: "selenium_manager" | "webdriver_manager"
            use_grid:    True → remote WebDriver via Selenium Grid hub
                         False → local browser (default)
            grid_url:    Grid hub URL, e.g. "http://localhost:4444/wd/hub"

        Returns:
            A ready-to-use WebDriver instance with timeouts configured.
        """
        # Use settings as defaults, allow override per-call
        browser     = (browser     or settings.browser    ).lower()
        headless    = headless     if headless is not None else settings.headless
        driver_mode = driver_mode  or settings.driver_mode
        use_grid    = use_grid     if use_grid  is not None else settings.use_grid
        grid_url    = grid_url     or settings.grid_url

        log.info(
            "Creating WebDriver | browser=%s | headless=%s | mode=%s | grid=%s",
            browser, headless, driver_mode, use_grid,
        )

        if use_grid:
            # ── Remote execution via Selenium Grid ────────────────────────────
            driver = DriverFactory._create_remote(browser, headless, grid_url)
        elif browser == "chrome":
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

    # ── Remote (Selenium Grid) ─────────────────────────────────────────────────

    @staticmethod
    def _create_remote(browser: str, headless: bool, grid_url: str):
        """
        Create a remote WebDriver that executes on a Selenium Grid node.

        CONCEPT: webdriver.Remote() sends WebDriver commands over HTTP to
        the Grid hub, which forwards them to a registered browser node.
        The test code is identical — only the driver creation differs.

        Args:
            browser: "chrome" or "firefox"
            headless: passed to the option builder (Grid nodes support headless)
            grid_url: full hub URL, e.g. "http://selenium-hub:4444/wd/hub"
        """
        if browser == "chrome":
            options = _build_chrome_options(headless, is_remote=True)   # ← is_remote=True avoids port 9222 conflict on Grid
        elif browser == "firefox":
            options = _build_firefox_options(headless)
        else:
            raise ValueError(f"Unsupported browser for Grid: '{browser}'.")

        log.info("Remote WebDriver | grid=%s | browser=%s | headless=%s", grid_url, browser, headless)
        return webdriver.Remote(command_executor=grid_url, options=options)
