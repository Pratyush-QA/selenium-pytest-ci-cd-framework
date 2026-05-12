# =============================================================================
# Dockerfile — UI Selenium framework in Docker with Chrome headless
# =============================================================================
#
# CONCEPT: Running Selenium in Docker
# ────────────────────────────────────
# Normal Selenium needs a real desktop + browser installed.
# Docker solves this by bundling Chrome + ChromeDriver into the image.
#
# We use the official Selenium standalone Chrome image as our base.
# It provides:
#   - Google Chrome (stable)
#   - ChromeDriver (matching version, auto-managed)
#   - Xvfb virtual framebuffer (for headed mode inside Docker)
#   - VNC + noVNC for watching tests live in a browser
#
# BUILD:
#   docker build -t ui-automation-framework .
#
# RUN ALL TESTS (headless):
#   docker run --rm ui-automation-framework
#
# RUN SMOKE ONLY:
#   docker run --rm -e PYTEST_ARGS="-m smoke" ui-automation-framework
#
# RUN HEADED (with VNC, see below via docker-compose):
#   docker-compose up tests-headed
# =============================================================================

FROM python:3.11-slim

LABEL description="Selenium + Pytest UI Automation Framework"
LABEL target="https://the-internet.herokuapp.com"

# ── Environment ───────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=ci \
    HEADLESS=true \
    PYTEST_ARGS="" \
    DISPLAY=:99

# ── Install Chrome + ChromeDriver + system deps ───────────────────────────────
# CONCEPT: We install Chrome directly in the image.
# Selenium Manager (Selenium 4.6+) auto-downloads ChromeDriver at runtime
# matching the installed Chrome version — no version pinning needed.
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget \
        curl \
        gnupg \
        unzip \
        ca-certificates \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        xdg-utils \
    # curl + jq are needed by runner.sh to poll the Selenium Grid hub readiness endpoint
    jq \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy project ──────────────────────────────────────────────────────────────
COPY . .
RUN chmod +x runner.sh \
    && mkdir -p screenshots reports logs allure-results

# ── Default: run tests locally (headless). Use runner.sh when targeting Grid. ─
CMD ["sh", "-c", "pytest ${PYTEST_ARGS} --headless"]
