#!/bin/bash
# =============================================================================
# run.sh — Scale browser nodes and run test suites
# =============================================================================
#
# CONCEPT: Dynamic browser scaling
# ──────────────────────────────────
# Instead of hardcoding the number of browser containers, run.sh lets you:
#   1. Start the Grid with N chrome containers
#   2. Run tests with BROWSER=chrome
#   3. Then scale up firefox and rerun with BROWSER=firefox
#
# This is useful for cross-browser testing without keeping all containers
# running at the same time.
# =============================================================================

# ── Run tests on Chrome with 2 Chrome nodes ──────────────────────────────────
echo "Starting Grid with 2 Chrome nodes..."
docker-compose -f grid.yaml up --scale chrome=2 -d

echo "Running test suites on Chrome..."
BROWSER=chrome docker-compose up --build

# ── Swap to Firefox with 2 Firefox nodes ─────────────────────────────────────
echo "Switching to Firefox with 2 Firefox nodes..."
docker-compose -f grid.yaml up --scale firefox=2 -d

echo "Running test suites on Firefox..."
BROWSER=firefox docker-compose up

# ── Teardown ──────────────────────────────────────────────────────────────────
echo "Tearing down..."
docker-compose -f grid.yaml down
docker-compose down
