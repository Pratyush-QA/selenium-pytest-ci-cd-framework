# Final docker-compose.yml Notes

This file is the final framework-level Docker Compose file for the Python Selenium project.
Think of it like a control panel: from one YAML file we can run tests in local Docker mode, Selenium Grid mode, parallel mode, and Allure report mode.

File location:

```text
C:\docker_test\workspace\05-dockerize\python-selenium\docker-compose.yml
```

## Main Objective

Earlier folders taught one concept at a time:

- `01-running-tests`: run pytest inside a Docker container.
- `02-grid-and-test-suites`: run test suites against Selenium Grid.
- `03-providing-test-data`: pass/mount test data into containers.
- `04-scale-browser`: scale browser nodes and understand Grid capacity.

This final `docker-compose.yml` combines the useful parts into one framework-level file.
It lets you choose what you want to run by using Compose profiles.

## Why Profiles Are Used

All runnable services are behind profiles:

- `local`
- `grid`
- `report`

Because of this, plain command:

```powershell
docker compose up
```

will not start all test services accidentally.
That is why `docker compose config` may show:

```text
services: {}
```

That is expected. Services appear only when you enable a profile.

Example:

```powershell
docker compose --profile local config --services
```

shows local services like:

```text
tests
smoke
regression
parallel
```

## Common Commands

Go to the final framework folder:

```powershell
cd C:\docker_test\workspace\05-dockerize\python-selenium
```

Run local smoke tests:

```powershell
docker compose --profile local up --build smoke
```

Run local regression tests:

```powershell
docker compose --profile local up --build regression
```

Run all local tests:

```powershell
docker compose --profile local up --build tests
```

Run local tests in parallel:

```powershell
docker compose --profile local up --build parallel
```

Run smoke tests on Selenium Grid:

```powershell
docker compose --profile grid up --build grid-tests
```

Open Grid UI:

```text
http://localhost:4444
```

Open noVNC browser view:

```text
http://localhost:7900
```

Run Allure report server:

```powershell
docker compose --profile report up allure-server
```

Open Allure UI:

```text
http://localhost:8082
```

Stop and remove containers/networks:

```powershell
docker compose --profile local --profile grid --profile report down
```

## docker compose up vs Specific Service

If you run:

```powershell
docker compose --profile local up
```

Compose starts all services inside the `local` profile:

- `tests`
- `smoke`
- `regression`
- `parallel`

That is usually not what we want.

If you run:

```powershell
docker compose --profile local up smoke
```

Compose starts only the `smoke` service.

For Grid:

```powershell
docker compose --profile grid up grid-tests
```

Compose starts `grid-tests`, and because `grid-tests` has `depends_on`, Compose also starts:

- `selenium-hub`
- `chrome-node`

So yes, you can start one service, and Compose can automatically start its dependency services.

## What --build Means

Example:

```powershell
docker compose --profile local up --build smoke
```

`--build` tells Compose to rebuild the `python-selenium` image before starting the container.

Use `--build` when you changed:

- `Dockerfile`
- `requirements.txt`
- test code
- page objects
- config files
- `runner.sh`

Without `--build`, Compose may reuse an old image, and your latest changes may not be inside the container.

For learning, using `--build` is safer.

## image + build Flow

In the YAML we use both:

```yaml
image: python-selenium
build:
  context: .
  dockerfile: Dockerfile
```

Meaning:

- `build` tells Compose how to create the image.
- `image` gives the created image a fixed name: `python-selenium`.

If image is not present, Compose builds it.
If image is already present and you do not pass `--build`, Compose can reuse it.
If you pass `--build`, Compose rebuilds it first.

## Local Services

These services use Chrome inside the test container itself:

- `tests`
- `smoke`
- `regression`
- `parallel`

They do not use Selenium Grid.

Example service:

```yaml
smoke:
  command: pytest -m smoke --headless ...
```

Here Compose creates a test container from the `python-selenium` image and directly runs pytest inside it.
The browser is also inside this same container.

## Parallel Service

The `parallel` service runs:

```powershell
pytest -n auto --headless
```

Important point:

Scaling browser containers does not automatically make tests parallel.
Tests become parallel only when pytest is told to run parallel using `-n`, for example:

```powershell
pytest -n auto
```

So:

- Grid capacity = how many browser sessions Grid can accept.
- Pytest parallelism = how many tests pytest sends at the same time.

Both are different.

## Selenium Grid Services

Grid profile has three main services:

- `selenium-hub`
- `chrome-node`
- `grid-tests`

### selenium-hub

This is the central Grid server.
It receives WebDriver requests from tests.

Important port:

```yaml
4444:4444
```

Use this in browser:

```text
http://localhost:4444
```

Inside Docker network, containers do not use `localhost` for the hub.
They use service name:

```text
http://selenium-hub:4444/wd/hub
```

### chrome-node

This container provides real Chrome browser sessions to the Grid.
It registers itself with `selenium-hub` using these values:

```yaml
SE_EVENT_BUS_HOST: selenium-hub
SE_EVENT_BUS_PUBLISH_PORT: 4442
SE_EVENT_BUS_SUBSCRIBE_PORT: 4443
```

This setting gives Chrome more shared memory:

```yaml
shm_size: 2gb
```

This helps Chrome run more reliably inside Docker.

This setting allows more than the default session count:

```yaml
SE_NODE_OVERRIDE_MAX_SESSIONS: "true"
SE_NODE_MAX_SESSIONS: 2
```

Meaning one Chrome node can handle up to 2 sessions.
But again, tests will use multiple sessions only if pytest runs tests in parallel.

### grid-tests

This is the test runner for Grid mode.
It does not open browser locally inside its own container.
It sends WebDriver requests to Selenium Grid.

It uses:

```yaml
command: sh runner.sh
```

That means Docker Compose calls `runner.sh`.
Then `runner.sh` calls pytest.

Flow:

```text
docker compose up grid-tests
        |
        v
Compose starts selenium-hub and chrome-node
        |
        v
Compose starts grid-tests
        |
        v
grid-tests runs: sh runner.sh
        |
        v
runner.sh waits until hub is ready
        |
        v
runner.sh runs pytest with --grid and --grid-url
```

## Why runner.sh Is Needed If depends_on Exists

`depends_on` only controls start order.
It means:

```text
Start hub container before test container.
```

But it does not guarantee:

```text
Hub is fully ready to accept WebDriver sessions.
```

So `runner.sh` performs readiness check:

```text
http://selenium-hub:4444/status
```

Only after Grid says ready, it starts pytest.

Without this, tests may start too early and fail randomly.

## command Overrides Dockerfile CMD

Dockerfile can define a default command.
But in Compose, this line:

```yaml
command: sh runner.sh
```

or this:

```yaml
command: pytest -m smoke ...
```

overrides the Dockerfile default command for that service.

So each service can run the same image in a different way.

## Passing Values From PowerShell

For Grid service, default values are:

```yaml
BROWSER: ${BROWSER:-chrome}
TEST_SUITE: ${TEST_SUITE:-smoke}
PYTEST_ARGS: ${PYTEST_ARGS:-}
```

Default means if you do not provide anything, it uses:

- browser: `chrome`
- suite: `smoke`

PowerShell example to override suite:

```powershell
$env:TEST_SUITE="regression"
docker compose --profile grid up --build grid-tests
```

PowerShell example to add pytest parallel execution:

```powershell
$env:PYTEST_ARGS="-n auto"
docker compose --profile grid up --build grid-tests
```

Clear env variables after testing:

```powershell
Remove-Item Env:\TEST_SUITE
Remove-Item Env:\PYTEST_ARGS
```

## Volumes

The YAML maps host folders to container folders:

```yaml
./screenshots:/app/screenshots
./reports:/app/reports
./allure-results:/app/allure-results
./logs:/app/logs
```

Meaning:

- container writes report inside `/app/reports`
- file appears on your Windows machine inside `./reports`

This is why Docker Desktop File Sharing for `C:\docker_test` matters.
If Docker cannot access that Windows path, volume mapping can fail.

## Reports

HTML reports are created in:

```text
reports/
```

Allure raw results are created in:

```text
allure-results/
```

Allure server reads:

```yaml
./allure-results:/app/allure-results
```

and shows report UI at:

```text
http://localhost:8082
```

Allure does not run tests.
It only converts test results into a readable report dashboard.

## Best Verification Commands

For local smoke verification:

```powershell
docker compose --profile local up --build --abort-on-container-exit --exit-code-from smoke smoke
```

For Grid smoke verification:

```powershell
docker compose --profile grid up --build --abort-on-container-exit --exit-code-from grid-tests grid-tests
```

Why these extra flags are useful:

- `--abort-on-container-exit`: stop Compose when the test container finishes.
- `--exit-code-from smoke`: return pass/fail based on the test container.
- `--exit-code-from grid-tests`: same idea for Grid mode.

These flags are useful for CI/CD because Jenkins needs a real pass/fail exit code.

## Final Mental Model

Use this simple mental model:

```text
Dockerfile = how to build the Python Selenium test image

docker-compose.yml = how to run that image in different modes

local profile = test container runs pytest and browser inside same container

grid profile = test container runs pytest, browser runs in Selenium Grid node

runner.sh = waits for Grid readiness, then starts pytest

report profile = starts Allure server to view generated Allure results
```

## Which Mode Should I Use?

For quick framework check:

```powershell
docker compose --profile local up --build smoke
```

For learning Selenium Grid integration:

```powershell
docker compose --profile grid up --build grid-tests
```

For learning parallel execution locally:

```powershell
docker compose --profile local up --build parallel
```

For viewing report after execution:

```powershell
docker compose --profile report up allure-server
```
