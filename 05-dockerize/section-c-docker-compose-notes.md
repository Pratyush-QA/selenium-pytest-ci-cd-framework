# Section C - docker-compose.yml Notes

File explained:

```text
C:\docker_test\workspace\05-dockerize\python-selenium\docker-compose.yml
```

## 1. What This Compose File Does

This compose file helps run the Python Selenium framework using Docker services.

It supports:

```text
standalone test containers
optional Selenium Grid services
optional Allure report service
```

Important:

```text
Dockerfile builds one image.
docker-compose.yml defines how containers/services are started from images.
```

Simple:

```text
Dockerfile      -> how to build image
docker-compose  -> how to run one or more containers together
```

## 2. version

```yaml
version: "3.9"
```

This tells Docker Compose which compose file format is being used.

Simple:

```text
Use Docker Compose syntax version 3.9.
```

## 3. x-base Template

```yaml
x-base: &base
```

This is a reusable YAML template.

Important:

```text
x-base is not a container.
x-base is not a service.
It only stores common configuration.
```

Why use it?

```text
tests, smoke, regression, and parallel services need many same settings.
Instead of repeating those settings, we define them once in x-base.
```

## 4. build Section

```yaml
build:
  context: .
  dockerfile: Dockerfile
```

Meaning:

```text
Build image from current folder.
Use Dockerfile from current folder.
```

Here current folder is:

```text
C:\docker_test\workspace\05-dockerize\python-selenium
```

So Compose will use:

```text
C:\docker_test\workspace\05-dockerize\python-selenium\Dockerfile
```

Simple:

```text
build = create image from Dockerfile
```

## 5. image vs build

Compose services can use either `build` or `image`.

### build

```yaml
build:
  context: .
  dockerfile: Dockerfile
```

Meaning:

```text
Build custom image from local Dockerfile.
```

Used for:

```text
your test framework image
```

### image

```yaml
image: selenium/hub:4.18.1
```

Meaning:

```text
Use existing image from local Docker storage or pull from registry.
```

Used for:

```text
selenium-hub
chrome-node
allure-server
```

Simple:

```text
build -> our custom image
image -> ready-made image
```

## 6. Common Environment Variables

```yaml
environment:
  - ENV=${ENV:-ci}
  - HEADLESS=true
  - PYTHONPATH=/app
```

These variables are passed into the container at runtime.

```text
ENV=${ENV:-ci}  -> use host ENV if available, otherwise ci
HEADLESS=true   -> browser should run headless
PYTHONPATH=/app -> Python can import project modules from /app
```

This syntax:

```yaml
${ENV:-ci}
```

means:

```text
If ENV is passed from host/CI, use that.
If ENV is not passed, use ci.
```

Example:

```bash
ENV=qa docker compose up smoke
```

Then inside container:

```text
ENV=qa
```

If no ENV is passed:

```text
ENV=ci
```

## 7. Common Volumes

```yaml
volumes:
  - ./screenshots:/app/screenshots
  - ./reports:/app/reports
  - ./allure-results:/app/allure-results
  - ./logs:/app/logs
```

Volume mapping means:

```text
host folder : container folder
```

Example:

```yaml
./reports:/app/reports
```

Meaning:

```text
If container writes /app/reports/report.html,
the file appears on host machine in ./reports/report.html.
```

Why use volumes?

```text
Containers are temporary.
Reports/screenshots/logs should remain on host after container exits.
```

So these folders are mounted:

```text
screenshots     -> failed screenshots
reports         -> HTML reports
allure-results  -> Allure data
logs            -> automation logs
```

## 8. Common Network

```yaml
networks:
  - ui-test-network
```

This connects the service to the Docker network named `ui-test-network`.

Containers on the same network can communicate by service/container name.

Example:

```text
chrome-node can talk to selenium-hub using selenium-hub name.
```

## 9. YAML Merge: <<: *base

Example:

```yaml
tests:
  <<: *base
```

Meaning:

```text
Copy all common settings from x-base into this service.
```

So `tests`, `smoke`, `regression`, and `parallel` all reuse:

```text
build
environment
volumes
networks
```

Simple:

```text
&base defines reusable block.
*base uses that block.
<< merges that block into service.
```

## 10. command

Example:

```yaml
command: >
  pytest --headless
  --alluredir=allure-results
  --html=reports/report.html
  --self-contained-html
  -v
```

`command` overrides Dockerfile `CMD`.

Dockerfile has:

```dockerfile
CMD ["sh", "-c", "pytest ${PYTEST_ARGS} --headless"]
```

But when compose service has `command`, Dockerfile CMD does not run.

Simple:

```text
Dockerfile CMD -> default command
compose command -> service-specific command
```

## 11. YAML > Multiline Command

```yaml
command: >
  pytest --headless
  --alluredir=allure-results
  -v
```

The `>` lets us write a long command across multiple lines.

Compose treats it like one line:

```bash
pytest --headless --alluredir=allure-results -v
```

Why use it?

```text
Better readability.
Long pytest commands are easier to read line by line.
```

## 12. tests Service

```yaml
tests:
  <<: *base
  container_name: ui-tests-all
  command: >
    pytest --headless
    --alluredir=allure-results
    --html=reports/report.html
    --self-contained-html
    -v
```

This service runs all tests.

Flow:

```text
Build/use python-selenium image
Start container named ui-tests-all
Run pytest command
Save reports/allure results using mounted volumes
Container exits after tests finish
```

This is standalone mode:

```text
pytest runs in test container
Chrome runs in same test container
No Selenium Grid is used
```

Command:

```bash
docker compose up tests
```

## 13. smoke Service

```yaml
smoke:
  <<: *base
  container_name: ui-tests-smoke
  command: >
    pytest -m smoke --headless
    --alluredir=allure-results
    --html=reports/smoke-report.html
    --self-contained-html
    -v
```

This service runs only smoke tests.

```text
-m smoke -> run tests marked with @pytest.mark.smoke
```

Flow:

```text
same image
same code
same mounted folders
different pytest marker
different report file
```

Command:

```bash
docker compose up smoke
```

## 14. regression Service

```yaml
regression:
  <<: *base
  container_name: ui-tests-regression
  command: >
    pytest -m regression --headless
    --alluredir=allure-results
    --html=reports/regression-report.html
    --self-contained-html
    -v
```

This service runs only regression tests.

```text
-m regression -> run tests marked with @pytest.mark.regression
```

Command:

```bash
docker compose up regression
```

## 15. parallel Service

```yaml
parallel:
  <<: *base
  container_name: ui-tests-parallel
  command: >
    pytest -n auto --headless
    --alluredir=allure-results
    -v
```

`-n auto` comes from `pytest-xdist`.

Meaning:

```text
Run tests in parallel using available CPU workers.
```

Important:

```text
Each worker may create its own browser instance.
Tests must be independent.
Avoid shared test data/state.
```

Command:

```bash
docker compose up parallel
```

## 16. selenium-hub Service

```yaml
selenium-hub:
  image: selenium/hub:4.18.1
  container_name: selenium-hub
  ports:
    - "4442:4442"
    - "4443:4443"
    - "4444:4444"
  networks:
    - ui-test-network
  profiles:
    - grid
```

This starts Selenium Grid Hub.

Hub responsibility:

```text
Receive WebDriver commands.
Route sessions/commands to registered browser nodes.
Show Grid UI.
```

Ports:

```text
4444 -> WebDriver endpoint and Grid UI
4442 -> event bus publish port
4443 -> event bus subscribe port
```

From host machine:

```text
http://localhost:4444/ui
```

Why `profiles: grid`?

```text
This service starts only when grid profile is enabled.
```

Example:

```bash
docker compose --profile grid up selenium-hub
```

## 17. chrome-node Service

```yaml
chrome-node:
  image: selenium/node-chrome:4.18.1
  container_name: selenium-chrome-node
  shm_size: 2gb
  depends_on:
    - selenium-hub
  environment:
    - SE_EVENT_BUS_HOST=selenium-hub
    - SE_EVENT_BUS_PUBLISH_PORT=4442
    - SE_EVENT_BUS_SUBSCRIBE_PORT=4443
    - SE_NODE_MAX_SESSIONS=2
  ports:
    - "7900:7900"
  networks:
    - ui-test-network
  profiles:
    - grid
```

This starts a Chrome browser node for Selenium Grid.

Browser actually runs inside this container.

### shm_size

```yaml
shm_size: 2gb
```

Chrome needs shared memory.

Without enough shared memory:

```text
Chrome may crash or become unstable inside container.
```

### depends_on

```yaml
depends_on:
  - selenium-hub
```

Meaning:

```text
Start chrome-node after selenium-hub container starts.
```

Important:

```text
depends_on does not guarantee Hub is fully ready.
It only controls startup order.
```

### Event Bus Environment Variables

```yaml
SE_EVENT_BUS_HOST=selenium-hub
SE_EVENT_BUS_PUBLISH_PORT=4442
SE_EVENT_BUS_SUBSCRIBE_PORT=4443
```

Meaning:

```text
Tell Chrome node how to register/connect with Selenium Hub.
```

`selenium-hub` is service/container name on the Docker network.

### Max Sessions

```yaml
SE_NODE_MAX_SESSIONS=2
```

Meaning:

```text
Allow up to 2 concurrent Chrome sessions on this node.
```

### noVNC Port

```yaml
ports:
  - "7900:7900"
```

Allows watching browser live from host:

```text
http://localhost:7900
```

## 18. profiles

Profiles let us keep optional services in the same compose file without starting them every time.

Example:

```yaml
profiles:
  - grid
```

Meaning:

```text
Start this service only when --profile grid is used.
```

Without profile:

```bash
docker compose up smoke
```

starts only the `smoke` service and required dependencies.

With profile:

```bash
docker compose --profile grid up selenium-hub chrome-node
```

starts Grid-related services.

## 19. allure-server Service

```yaml
allure-server:
  image: frankescobar/allure-docker-service:latest
  container_name: allure-server
  environment:
    CHECK_RESULTS_EVERY_SECONDS: 3
    KEEP_HISTORY: 1
  ports:
    - "8080:5050"
  volumes:
    - ./allure-results:/app/allure-results
  networks:
    - ui-test-network
  profiles:
    - report
```

This starts an Allure report server.

It reads test result files from:

```text
./allure-results
```

because this volume maps:

```yaml
./allure-results:/app/allure-results
```

Port mapping:

```yaml
"8080:5050"
```

Meaning:

```text
host localhost:8080 -> container port 5050
```

Open:

```text
http://localhost:8080
```

Profile:

```yaml
profiles:
  - report
```

Start with:

```bash
docker compose --profile report up allure-server
```

## 20. networks Section

```yaml
networks:
  ui-test-network:
    driver: bridge
```

This creates a bridge network.

Simple:

```text
Containers attached to ui-test-network can talk to each other internally.
```

Example:

```text
chrome-node -> selenium-hub
```

using service name:

```text
selenium-hub
```

## 21. Important Clarification About This Compose File

In this exact file:

```text
tests
smoke
regression
parallel
```

run standalone pytest commands:

```text
pytest --headless
pytest -m smoke --headless
pytest -m regression --headless
pytest -n auto --headless
```

They do not use:

```text
runner.sh
--grid
--grid-url
```

So these services run:

```text
pytest inside test container
Chrome inside same test container
```

Grid services are present:

```text
selenium-hub
chrome-node
```

But this file does not currently define a `grid-tests` service that runs:

```text
command: sh runner.sh
```

For a clearer Grid + runner.sh example, see:

```text
C:\docker_test\workspace\05-dockerize\02-grid-and-test-suites\docker-compose.yaml
```

## 22. Common Commands

Run all tests:

```bash
docker compose up tests
```

Run smoke tests:

```bash
docker compose up smoke
```

Run regression tests:

```bash
docker compose up regression
```

Run parallel tests:

```bash
docker compose up parallel
```

Build images:

```bash
docker compose build
```

Build and run:

```bash
docker compose up --build smoke
```

Start Grid profile services:

```bash
docker compose --profile grid up selenium-hub chrome-node
```

Start Allure report server:

```bash
docker compose --profile report up allure-server
```

Stop/remove containers and network:

```bash
docker compose down
```

## 23. Final One-Line Summary

```text
This docker-compose.yml defines reusable test services, optional Selenium Grid services, report volumes, network wiring, and service-specific pytest commands for running the framework in Docker.
```
