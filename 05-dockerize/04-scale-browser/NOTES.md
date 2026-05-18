# 04 - Scale Browser Notes

## Objective

This folder teaches dynamic browser scaling in Selenium Grid.

Instead of always running Chrome and Firefox nodes together, we start the Grid, scale Chrome nodes, run tests on Chrome, then scale Chrome down and scale Firefox up, and run the same tests again on Firefox.

```text
grid.yaml             = Grid infrastructure: hub + browser nodes
docker-compose.yaml   = test runner services only
run.sh                = controls browser scaling and test execution flow
```

## Compared With 03-providing-test-data

`03-providing-test-data` uses one compose file:

```text
hub + chrome + firefox + smoke-tests + login-tests
```

It teaches how to mount external test data into containers.

`04-scale-browser` splits the responsibility:

```text
grid.yaml             -> start and scale Grid infrastructure
docker-compose.yaml   -> run test services
run.sh                -> decide Chrome first, then Firefox
```

It teaches scaling and cross-browser execution.

## Why Two Compose Files?

We split files so browser infrastructure and tests can be controlled separately.

```bash
docker compose -f grid.yaml up --scale chrome=2 -d
```

This starts only the Grid/browser side.

```bash
BROWSER=chrome docker compose -f docker-compose.yaml up --build
```

This runs only test containers and tells them to request Chrome from the Grid.

## Why Use `-f grid.yaml`?

`grid.yaml` is not a default compose filename, so Docker Compose will not pick it automatically.

You must specify it:

```bash
docker compose -f grid.yaml up
```

`docker-compose.yaml` is a default compose filename, so this also works:

```bash
docker compose up
```

But for learning, this is clearer:

```bash
docker compose -f docker-compose.yaml up
```

## Meaning Of `BROWSER=chrome docker compose ...`

This is Bash syntax.

```bash
BROWSER=chrome docker compose -f docker-compose.yaml up --build
```

It means:

```text
For this command only, set BROWSER=chrome.
Docker Compose reads ${BROWSER} from docker-compose.yaml.
The test container receives BROWSER=chrome.
runner.sh runs pytest --browser chrome.
```

PowerShell equivalent:

```powershell
$env:BROWSER="chrome"
docker compose -f docker-compose.yaml up --build
```

## `docker compose up` vs `docker compose up --build`

```bash
docker compose up
```

Starts containers using the existing image if it already exists.

```bash
docker compose up --build
```

Rebuilds the image first, then starts containers.

Use `--build` when you changed Python code, Dockerfile, requirements, runner.sh, config, or tests.

## `--scale chrome=2` vs `SE_NODE_MAX_SESSIONS=4`

They are different.

```bash
--scale chrome=2
```

Means create 2 Chrome node containers.

```yaml
SE_NODE_MAX_SESSIONS=4
```

Means each Chrome node container can run 4 browser sessions.

Total capacity:

```text
2 Chrome containers x 4 sessions each = 8 Chrome sessions
```

Think of it like this:

```text
--scale chrome=2       = 2 classrooms
SE_NODE_MAX_SESSIONS=4 = 4 students per classroom
Total                  = 8 students
```

## Port 4444 Reminder

`grid.yaml` maps the Grid hub to your machine:

```yaml
ports:
  - "4444:4444"
```

If another Grid is already running, you may see:

```text
Bind for 0.0.0.0:4444 failed: port is already allocated
```

Fix:

```powershell
docker ps
```

Then stop the old compose project, for example:

```powershell
cd C:\docker_test\workspace\05-dockerize\03-providing-test-data
docker compose down
```

## Commands To Run

### Git Bash or WSL

```bash
cd /c/docker_test/workspace/05-dockerize/04-scale-browser
sh run.sh
```

### PowerShell Manual Flow

```powershell
cd C:\docker_test\workspace\05-dockerize\04-scale-browser

docker compose -f grid.yaml up --scale chrome=2 --scale firefox=0 -d
$env:BROWSER="chrome"
docker compose -f docker-compose.yaml up --build

docker compose -f grid.yaml up --scale chrome=0 --scale firefox=2 -d
$env:BROWSER="firefox"
docker compose -f docker-compose.yaml up --build

docker compose -f docker-compose.yaml down
docker compose -f grid.yaml down
```

## Final Mental Model

```text
run.sh
  -> starts Grid with Chrome capacity
  -> runs tests with BROWSER=chrome
  -> swaps capacity to Firefox
  -> runs same tests with BROWSER=firefox
  -> cleans up
```

This is the Dockerized way to run the same automation suite across browsers while controlling how many browser containers are available.
## `image` + `build` + `--build` Flow

In `docker-compose.yaml`, each test service has both:

```yaml
image: python-selenium
build:
  context: ../python-selenium
```

This means:

```text
Build the image from ../python-selenium/Dockerfile,
but name/tag the final image as python-selenium.
```

If the image does not exist:

```text
docker compose up --build
  -> builds image from ../python-selenium
  -> tags it as python-selenium
  -> starts smoke-tests and regression-tests containers
```

If the image already exists:

```text
docker compose up --build
  -> still rebuilds/checks the image first
  -> Docker cache may make it fast
  -> starts containers using the refreshed python-selenium image
```

If you run without `--build`:

```text
docker compose up
  -> if python-selenium exists, use existing image
  -> if image is missing, build it from build context
```

Why keep both `image` and `build`?

```text
image: python-selenium  -> gives a clean reusable image name
build: ../python-selenium -> tells Compose how to create that image
```

Without `image`, Compose creates an automatic project/service-based image name. With `image`, the name is predictable: `python-selenium`.
## Why Two Compose Files If We Already Have `runner.sh`?

This is the key distinction:

```text
runner.sh      = readiness check
2 compose files = lifecycle/control separation
```

`runner.sh` answers this question:

```text
Is the Selenium Grid hub ready to accept WebDriver requests?
```

It prevents this issue:

```text
container started, but hub service not ready yet -> test fails with connection refused
```

The two compose files answer a different question:

```text
Can I manage Grid infrastructure separately from test runner containers?
```

So these two files are not required because of readiness. Readiness is already handled by `runner.sh`.

They are used to keep responsibilities separate:

```text
grid.yaml             = long-running infrastructure: hub, chrome nodes, firefox nodes
docker-compose.yaml   = short-running test jobs: smoke-tests, regression-tests
```

Could this be done with a single compose file?

Yes.

A single compose file with `runner.sh` would still work.

But with one file, infra and test jobs are mixed together:

```text
hub
chrome
firefox
smoke-tests
regression-tests
```

Then when you only want to scale browser nodes, you must be careful not to start test jobs accidentally.

With two files:

```bash
docker compose -f grid.yaml up --scale chrome=2 -d
```

means:

```text
Only Grid infrastructure starts or changes.
No tests run.
```

And:

```bash
BROWSER=chrome docker compose -f docker-compose.yaml up --build
```

means:

```text
Only test containers run.
They connect to the already-running Grid.
```

Final rule:

```text
runner.sh is for WHEN to start tests.
2 compose files are for WHAT to start and control separately.
```

So two files are not mandatory, but they make the scaling example cleaner and easier to reason about.
## Grid Scaling vs Pytest Parallel Execution

Scaling the Grid only creates browser capacity. It does not make pytest run tests in parallel by itself.

```text
Grid scaling = how many browser sessions are available
pytest -n    = how many tests run at the same time
```

Example:

```text
--scale chrome=2
SE_NODE_MAX_SESSIONS=4
```

Total Chrome capacity:

```text
2 Chrome node containers x 4 sessions each = 8 available browser sessions
```

But without pytest-xdist:

```bash
pytest -m regression
```

Tests still run mostly one by one.

To actually use multiple Grid sessions, run pytest with `-n`:

```bash
pytest -m regression -n 4
```

Then up to 4 tests can run at the same time, and each worker can create its own browser session.

Final rule:

```text
Scale Grid to provide capacity.
Use pytest -n to consume that capacity.
```
