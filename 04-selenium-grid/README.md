# 04 - Selenium Grid

A step-by-step learning project for running Selenium tests on a distributed Grid using Docker.

---

## Folder Structure

```
04-selenium-grid/
├── 01-simple-grid/              # Basic hub + Chrome + Firefox nodes
├── 02-scale-container/          # Scale nodes using Docker replicas
├── 03-max-sessions/             # Allow multiple concurrent sessions per node
├── 04-vnc-no-password/          # Watch tests live via browser (noVNC)
└── 05-ui-automation-framework/  # Full Selenium framework with Grid support
```

Each folder builds on the previous one — start from `01` and work your way to `05`.

---

## Learning Flow

### Step 1 — Start with a simple Grid (`01-simple-grid`)

Spin up a basic Selenium Grid with one hub and one Chrome + Firefox node.

```bash
cd 01-simple-grid
docker-compose up -d
```

- Hub is available at: `http://localhost:4444`
- Grid console (see registered nodes): `http://localhost:4444/ui`

Stop the Grid:
```bash
docker-compose down
```

---

### Step 2 — Scale the nodes (`02-scale-container`)

Same Grid but with 4 replicas of Chrome and Firefox — useful for running tests in parallel.

```bash
cd 02-scale-container
docker-compose up -d
```

Each browser gets 4 containers. The hub distributes test sessions across them automatically.

---

### Step 3 — Increase sessions per node (`03-max-sessions`)

Instead of more containers, allow each node to handle up to 4 concurrent sessions.

```bash
cd 03-max-sessions
docker-compose up -d
```

Key environment variables used:
```
SE_NODE_OVERRIDE_MAX_SESSIONS=true
SE_NODE_MAX_SESSIONS=4
```

---

### Step 4 — Watch tests run live (`04-vnc-no-password`)

Adds `SE_VNC_NO_PASSWORD=1` so you can watch the browser inside the container via noVNC — no password required.

```bash
cd 04-vnc-no-password
docker-compose up -d
```

Open your browser and go to:
- Chrome node: `http://localhost:7900`
- Firefox node: `http://localhost:7901`

You will see a live view of the browser as tests execute.

---

### Step 5 — Run the framework against the Grid (`05-ui-automation-framework`)

The framework is a full Selenium + Pytest project with Grid support built in.

**First, start a Grid** (use any of the above — `04-vnc-no-password` is recommended so you can watch):

```bash
cd 04-vnc-no-password
docker-compose up -d
```

**Then, in a new terminal, go to the framework and run tests:**

```bash
cd 05-ui-automation-framework

# Install dependencies (first time only)
pip install -r requirements.txt
pip install -e .

# Run smoke tests on the Grid
pytest -m smoke --grid --grid-url http://localhost:4444/wd/hub -v

# Run all tests on the Grid
pytest --grid --grid-url http://localhost:4444/wd/hub -v

# Run in headless mode on the Grid
pytest --grid --grid-url http://localhost:4444/wd/hub --headless -v

# Run without Grid (local browser)
pytest -m smoke -v
```

**Watch tests live:**
While tests run, open `http://localhost:7900` in your browser to see Chrome executing the test steps in real time.

---

## How Grid + Framework Work Together

```
Your Machine                        Docker Containers
─────────────────                   ──────────────────────────────────────
pytest --grid                ──►    selenium-hub (port 4444)
  └─ DriverFactory                      └─ routes to available node
       └─ webdriver.Remote  ──►    chrome-node
                                       └─ runs Chrome, executes test steps
                                       └─ noVNC (port 7900) ◄── watch live
```

1. `--grid` tells the framework to use `webdriver.Remote` instead of a local browser
2. The hub receives WebDriver commands and forwards them to a registered node
3. The Chrome node executes the commands inside a Docker container
4. Test results come back to your terminal as if running locally

---

## Quick Reference

| Command | What it does |
|---------|-------------|
| `docker-compose up -d` | Start Grid in background |
| `docker-compose down` | Stop and remove Grid containers |
| `docker-compose ps` | Check running containers |
| `docker-compose logs -f` | Stream container logs |
| `docker-compose up -d --scale chrome=3` | Scale Chrome to 3 nodes |
| `pytest --grid --grid-url http://localhost:4444/wd/hub` | Run tests on Grid |
| `pytest -m smoke` | Run smoke tests only |
| `pytest -m regression` | Run regression tests only |
| `pytest -n auto` | Run tests in parallel (local) |

---

## Grid Console

When the Grid is running, open `http://localhost:4444/ui` to see:
- Registered nodes and their browser/version
- Active sessions
- Queued sessions
- Node capacity and utilisation
