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
