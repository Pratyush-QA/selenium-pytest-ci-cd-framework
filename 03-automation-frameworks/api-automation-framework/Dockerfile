# =============================================================================
# Dockerfile — Run the pytest API framework inside a Docker container
# =============================================================================
#
# CONCEPT: Docker gives you a reproducible, isolated environment so:
#   - Tests run identically on any developer's machine
#   - CI/CD pipelines don't need Python installed on the runner
#   - You can pin exact dependency versions permanently
#
# BUILD THE IMAGE:
#   docker build -t pytest-api-framework .
#
# RUN ALL TESTS:
#   docker run --rm pytest-api-framework
#
# RUN ONLY SMOKE TESTS:
#   docker run --rm -e PYTEST_ARGS="-m smoke" pytest-api-framework
#
# RUN WITH A DIFFERENT ENVIRONMENT:
#   docker run --rm -e ENV=staging pytest-api-framework
#
# GENERATE ALLURE RESULTS:
#   docker run --rm -v $(pwd)/allure-results:/app/allure-results \
#              pytest-api-framework pytest --alluredir=allure-results
# =============================================================================

# ── Base image ────────────────────────────────────────────────────────────────
# Use official Python slim image. 'slim' is smaller than the full image
# but still includes pip and the standard library.
FROM python:3.11-slim

# ── Labels (metadata) ─────────────────────────────────────────────────────────
LABEL maintainer="API Framework"
LABEL description="Pytest API Automation Framework for JSONPlaceholder"
LABEL version="1.0"

# ── Environment variables ─────────────────────────────────────────────────────
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc bytecode files
# PYTHONUNBUFFERED: Ensures print/log output appears immediately in docker logs
# ENV: Which config.ini section to load (dev | staging | prod)
# PYTEST_ARGS: Extra args passed to pytest (e.g. "-m smoke --tb=long")
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=dev \
    PYTEST_ARGS=""

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Install OS dependencies ───────────────────────────────────────────────────
# We install curl for health checks and cleanup in the same RUN layer to
# keep the image small (fewer layers = smaller image).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Install Python dependencies ───────────────────────────────────────────────
# Copy requirements.txt BEFORE the rest of the source code.
# Docker caches layers — if requirements.txt hasn't changed, this expensive
# pip install step is skipped on subsequent builds.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Copy project source ───────────────────────────────────────────────────────
# Copy everything else. This is the last step so code changes don't
# invalidate the expensive pip install cache.
COPY . .

# ── Create directories that must exist at runtime ─────────────────────────────
RUN mkdir -p reports logs allure-results

# ── Default command ───────────────────────────────────────────────────────────
# This runs when you do `docker run pytest-api-framework` with no arguments.
# $PYTEST_ARGS lets you pass extra flags via -e PYTEST_ARGS="..."
CMD ["sh", "-c", "pytest ${PYTEST_ARGS}"]
