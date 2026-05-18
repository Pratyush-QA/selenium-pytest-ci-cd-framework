#!/bin/bash
# =============================================================================
# run.sh - Scale browser nodes and run test suites
# =============================================================================
# Objective:
#   1. Start Selenium Grid with only Chrome nodes.
#   2. Run the same test suites on Chrome.
#   3. Scale Chrome down, scale Firefox up.
#   4. Run the same test suites on Firefox.
#   5. Tear everything down.
#
# Run this file from Git Bash or WSL:
#   sh run.sh
# =============================================================================

# Run tests on Chrome with 2 Chrome node containers.
echo "Starting Grid with 2 Chrome nodes..."
docker compose -f grid.yaml up --scale chrome=2 --scale firefox=0 -d

echo "Running test suites on Chrome..."
BROWSER=chrome docker compose -f docker-compose.yaml up --build

# Switch to Firefox: remove Chrome nodes and start 2 Firefox node containers.
echo "Switching to Firefox with 2 Firefox nodes..."
docker compose -f grid.yaml up --scale chrome=0 --scale firefox=2 -d

echo "Running test suites on Firefox..."
BROWSER=firefox docker compose -f docker-compose.yaml up --build

# Tear down both compose files.
echo "Tearing down..."
docker compose -f docker-compose.yaml down
docker compose -f grid.yaml down
