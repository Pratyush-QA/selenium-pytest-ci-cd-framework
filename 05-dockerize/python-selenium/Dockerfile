# =============================================================================
# Dockerfile - UI Selenium framework in Docker with Chrome headless
# =============================================================================
# Objective:
#   Build a test-runner image containing Python, project dependencies,
#   Google Chrome, and matching ChromeDriver.
#
# Why install ChromeDriver in the image?
#   Selenium Manager can download ChromeDriver at runtime, but that requires
#   network/DNS inside the running container. Baking ChromeDriver into the image
#   makes docker run more stable and repeatable.
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

# Install Chrome, matching ChromeDriver, and system libraries required by Chrome.
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
    && install -d -m 0755 /etc/apt/keyrings \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
       | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && chmod a+r /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && CHROME_VERSION=$(google-chrome --product-version) \
    && echo "Installing ChromeDriver for Chrome ${CHROME_VERSION}" \
    && wget -q -O /tmp/chromedriver.zip "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chromedriver-linux64.zip" \
    && unzip -q /tmp/chromedriver.zip -d /tmp/chromedriver \
    && mv /tmp/chromedriver/chromedriver-linux64/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && chromedriver --version \
    && rm -rf /tmp/chromedriver /tmp/chromedriver.zip \
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

# Default: run tests locally inside this container. Compose can override this
# with `command: sh runner.sh` when the tests should target Selenium Grid.
CMD ["sh", "-c", "pytest ${PYTEST_ARGS} --headless"]