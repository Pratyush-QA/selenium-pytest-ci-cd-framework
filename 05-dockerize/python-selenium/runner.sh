#!/bin/bash
# =============================================================================
# runner.sh — Hub readiness check + test runner
# =============================================================================
#
# CONCEPT: Why do we need this script?
# ──────────────────────────────────────
# docker-compose `depends_on` only waits for a container to START, not for the
# service inside it to be READY. The Selenium Hub needs a few seconds after
# starting before it can accept WebDriver connections.
#
# If tests start before the hub is ready → ConnectionRefused → test failures.
#
# This script polls the hub's /status endpoint until it returns ready=true,
# then runs the tests. This is the standard "wait-for-it" pattern in Docker.
#
# ENVIRONMENT VARIABLES:
#   HUB_HOST     → Selenium Grid hub hostname (default: hub)
#   BROWSER      → chrome | firefox           (default: chrome)
#   TEST_SUITE   → pytest marker to run       (default: runs all tests)
#   PYTEST_ARGS  → any extra pytest flags
#
# USAGE (from docker-compose):
#   command: sh runner.sh
#
# DIRECT RUN (with Grid already up):
#   HUB_HOST=localhost BROWSER=chrome TEST_SUITE=smoke sh runner.sh
# =============================================================================

echo "-------------------------------------------"
echo "HUB_HOST   : ${HUB_HOST:-hub}"
echo "BROWSER    : ${BROWSER:-chrome}"
echo "TEST_SUITE : ${TEST_SUITE:-all}"
echo "-------------------------------------------"

# ── Wait for Selenium Grid Hub to be ready ────────────────────────────────────
# CONCEPT: curl fetches the hub's JSON status, jq parses out .value.ready.
# We loop until it equals "true" or we hit 30 attempts (30 seconds).
echo "Waiting for Selenium Grid hub..."
count=0
while [ "$(curl -s http://${HUB_HOST:-hub}:4444/status | jq -r .value.ready)" != "true" ]
do
  count=$((count + 1))
  echo "  Hub not ready. Attempt ${count}/30..."
  if [ "$count" -ge 30 ]; then
    echo "Hub did not become ready within 30 seconds. Exiting."
    exit 1
  fi
  sleep 1
done
echo "Selenium Grid is up and ready!"

# ── Run pytest against the Grid ───────────────────────────────────────────────
# CONCEPT: --grid routes WebDriver through the hub instead of a local browser.
# TEST_SUITE maps to a pytest marker (-m smoke, -m regression, etc.)
pytest \
  --grid \
  --grid-url "http://${HUB_HOST:-hub}:4444/wd/hub" \
  --browser "${BROWSER:-chrome}" \
  ${TEST_SUITE:+-m ${TEST_SUITE}} \
  ${PYTEST_ARGS} \
  -v
