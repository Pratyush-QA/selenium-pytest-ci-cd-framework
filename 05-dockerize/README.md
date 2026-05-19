# 05 - Dockerize Python Selenium Framework

Learn how to containerise a Selenium + Pytest framework and run tests against a Docker-based Selenium Grid.

This is the Python equivalent of the Java `selenium-docker/05-dockerize` project.

---

## Folder Structure

```
05-dockerize/
├── 01-running-tests/              # Run tests inside a Docker container (no Grid)
├── 02-grid-and-test-suites/       # Grid + two test suites running in parallel
├── 03-providing-test-data/        # Inject external test data via volume mounts
├── 04-scale-browser/              # Dynamically scale browser nodes
└── python-selenium/               # The Python Selenium framework (test code lives here)
```

---

## Key Concepts

### Dockerfile - Test Runner Image

The Dockerfile builds the Python Selenium test-runner image. It covers the base Python image, environment variables, Chrome/system dependencies, Python dependencies, project copy, output folders, and default test command.

Detailed Section A notes are here: [`section-a-dockerfile-notes.md`](./section-a-dockerfile-notes.md)

### runner.sh — Hub Readiness Check

The most important new concept in this module. `docker-compose depends_on` only waits for a container to **start**, not for the service inside it to be **ready**.

`runner.sh` is a shell script used by the test container to wait for Selenium Hub first, then run pytest against the Grid.

Detailed Section B notes are here: [`section-b-runner-sh-notes.md`](./section-b-runner-sh-notes.md)

`runner.sh` solves this by polling the hub's `/status` endpoint until it returns `ready: true`, then running pytest:

```bash
# From runner.sh
while [ "$(curl -s http://hub:4444/status | jq -r .value.ready)" != "true" ]
do
  sleep 1
done
pytest --grid --grid-url http://hub:4444/wd/hub -m smoke
```

### docker-compose.yml - Service Orchestration

The compose file defines how test containers, optional Selenium Grid services, networks, volumes, and report services are started together.

Detailed Section C notes are here: [`section-c-docker-compose-notes.md`](./section-c-docker-compose-notes.md)

### Environment Variables

All test behaviour is driven by environment variables — no code changes needed to switch browser or test suite:

| Variable | Default | Description |
|----------|---------|-------------|
| `HUB_HOST` | `hub` | Selenium Grid hub hostname |
| `BROWSER` | `chrome` | Browser to use: `chrome` or `firefox` |
| `TEST_SUITE` | all tests | pytest marker: `smoke`, `regression`, `login` etc. |
| `PYTEST_ARGS` | _(empty)_ | Any extra pytest flags |

---

## Learning Flow

### Step 1 — Run tests in Docker (no Grid)

```bash
cd 01-running-tests
# See README.md inside for commands
```

Just runs tests headless inside a single container. No hub, no nodes.

---

### Step 2 — Grid + two test suites

```bash
cd 02-grid-and-test-suites
docker-compose up --build
```

Starts: hub → chrome node → firefox node → smoke tests (Chrome) + login tests (Firefox) in parallel.

Both test services use `runner.sh` to wait for the hub before starting.

---

### Step 3 — External test data via volumes

```bash
cd 03-providing-test-data
# Edit test-data/config.json to change credentials or URLs
docker-compose up --build
```

`test-data/config.json` is mounted into the container at runtime.
Change the data, rerun — no image rebuild needed.

---

### Step 4 — Scale browser nodes

```bash
cd 04-scale-browser
sh run.sh
```

`run.sh` starts the grid with 2 Chrome containers, runs tests, then switches to 2 Firefox containers and reruns. Uses `${BROWSER}` env var to drive which browser each test service targets — same compose file, different browser.

---

## Running python-selenium Standalone

```bash
cd python-selenium

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run locally (no Docker, no Grid)
pytest -m smoke -v

# Run headless locally
pytest -m smoke --headless -v

# Run against a running Grid
pytest --grid --grid-url http://localhost:4444/wd/hub -m smoke -v
```

---

## Architecture

```
docker-compose up
    ├── hub (selenium/hub:4.18.1)
    │     └── exposes port 4444
    ├── chrome (selenium/node-chrome)  ← registered to hub
    ├── firefox (selenium/node-firefox) ← registered to hub
    ├── smoke-tests (python-selenium image)
    │     └── runner.sh
    │           ├── polls hub until ready
    │           └── pytest --grid -m smoke → hub → chrome node
    └── login-tests (python-selenium image)
          └── runner.sh
                ├── polls hub until ready
                └── pytest --grid -m login → hub → firefox node
```
