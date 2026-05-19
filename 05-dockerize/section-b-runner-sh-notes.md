# Section B - runner.sh Notes

File explained:

```text
C:\docker_test\workspace\05-dockerize\python-selenium\runner.sh
```

## 1. What runner.sh Does

`runner.sh` is used when tests run from a Docker test container and need to connect to Selenium Grid.

`runner.sh` is a shell script, similar idea to a `.py` file but written for the Linux shell.

```text
.py file  -> Python script, executed by Python
.sh file  -> shell script, executed by sh/bash
```

When we run:

```bash
sh runner.sh
```

it means:

```text
Use the sh program to read runner.sh line by line and execute each terminal command.
```

So commands inside `runner.sh`, like `echo`, `curl`, `sleep`, and `pytest`, are the same kind of commands we could type manually in terminal. We keep them in one file so Docker can run the full startup flow automatically.

The `while` loop inside `runner.sh` is also normal shell syntax. It can run inside the script or directly in a terminal.

Local terminal example:

```bash
count=0
while [ "$(curl -s http://localhost:4444/status | jq -r .value.ready)" != "true" ]
do
  count=$((count + 1))
  echo "Hub not ready. Attempt ${count}/30..."
  sleep 1
done
echo "Hub is ready"
```

URL difference:

```text
From local machine  -> http://localhost:4444/status
From test container -> http://hub:4444/status
```

So `runner.sh` mainly saves commands that we could type manually, then runs them automatically in the right order.

Simple flow:

```text
test container starts
runner.sh starts first
runner.sh waits for Selenium Hub to be ready
then runner.sh runs pytest
pytest sends browser commands to Hub
Hub routes commands to Chrome/Firefox node
```

Important:

```text
test container starts != tests start immediately
```

The test container starts, but `runner.sh` delays actual test execution until Hub is ready.

## 2. echo Command

`echo` prints messages in terminal/logs.

Example:

```bash
echo "Waiting for Selenium Grid hub..."
```

Output:

```text
Waiting for Selenium Grid hub...
```

In `runner.sh`:

```bash
echo "HUB_HOST   : ${HUB_HOST:-hub}"
echo "BROWSER    : ${BROWSER:-chrome}"
echo "TEST_SUITE : ${TEST_SUITE:-all}"
```

If environment values are:

```text
HUB_HOST=hub
BROWSER=chrome
TEST_SUITE=smoke
```

Then output is:

```text
HUB_HOST   : hub
BROWSER    : chrome
TEST_SUITE : smoke
```

Why use `echo`?

```text
To understand from logs which Hub, browser, and test suite are being used.
```

In CI/CD logs, `echo` is useful for debugging.

## 3. This Syntax: ${HUB_HOST:-hub}

```bash
${HUB_HOST:-hub}
```

Meaning:

```text
If HUB_HOST has value, use that value.
If HUB_HOST is empty/not set, use hub.
```

Examples:

```text
HUB_HOST=selenium-hub -> selenium-hub
HUB_HOST=hub          -> hub
HUB_HOST not set      -> hub
```

So this:

```bash
http://${HUB_HOST:-hub}:4444/status
```

usually becomes:

```text
http://hub:4444/status
```

inside Docker Compose.

## 4. Why We Use hub Instead of localhost

Inside a Docker container:

```text
localhost means the same container
```

So from test container:

```text
http://localhost:4444
```

means:

```text
test container itself on port 4444
```

But Selenium Hub is in a different container.

In Docker Compose, containers in the same network can call each other using service name.

Example:

```yaml
services:
  hub:
    image: selenium/hub

  smoke-tests:
    build:
      context: ../python-selenium
```

From `smoke-tests` container:

```text
http://hub:4444
```

goes to Hub container.

From your laptop:

```text
http://localhost:4444
```

works because compose maps the port:

```yaml
ports:
  - "4444:4444"
```

Simple rule:

```text
From host/laptop     -> use localhost:4444
From test container  -> use hub:4444
```

## 5. Why depends_on Is Not Enough

In compose:

```yaml
depends_on:
  - hub
```

means:

```text
Start this container after hub container starts.
```

But it does not mean:

```text
Selenium Hub is fully ready to accept WebDriver requests.
```

Container can be started, but application inside it may still be booting.

Example:

```text
Hub container started
Hub process still loading
Nodes still registering
Hub /status not ready yet
Test starts too early
Test fails with connection/session error
```

So `runner.sh` waits for real readiness:

```bash
curl -s http://${HUB_HOST:-hub}:4444/status | jq -r .value.ready
```

It waits until:

```text
ready = true
```

Then tests start.

## 6. Hub Readiness Check

This line checks Hub status:

```bash
curl -s http://${HUB_HOST:-hub}:4444/status | jq -r .value.ready
```

Breakdown:

```text
curl -> calls Hub status API
jq   -> reads one value from JSON response
```

Hub status API:

```text
http://hub:4444/status
```

Example JSON has:

```json
{
  "value": {
    "ready": true
  }
}
```

This:

```bash
jq -r .value.ready
```

extracts:

```text
true
```

The loop keeps checking:

```bash
while [ "$(curl -s http://${HUB_HOST:-hub}:4444/status | jq -r .value.ready)" != "true" ]
do
  echo "Hub not ready..."
  sleep 1
done
```

Meaning:

```text
If Hub is not ready, wait.
If Hub is ready, exit loop and run pytest.
```

## 7. Pytest Command

In `runner.sh`:

```bash
pytest \
  --grid \
  --grid-url "http://${HUB_HOST:-hub}:4444/wd/hub" \
  --browser "${BROWSER:-chrome}" \
  ${TEST_SUITE:+-m ${TEST_SUITE}} \
  ${PYTEST_ARGS} \
  -v
```

The backslash `\` means:

```text
command continues on next line
```

So it is one command, written in multiple lines for readability.

If values are:

```text
HUB_HOST=hub
BROWSER=chrome
TEST_SUITE=smoke
PYTEST_ARGS=
```

Final command becomes:

```bash
pytest --grid --grid-url http://hub:4444/wd/hub --browser chrome -m smoke -v
```

Meaning:

```text
pytest       -> run Python test cases
--grid       -> use Selenium Grid instead of local browser
--grid-url   -> Hub WebDriver URL
--browser    -> request chrome/firefox browser
-m smoke     -> run tests marked smoke only
PYTEST_ARGS  -> add extra pytest options at runtime
-v           -> verbose output
```

## 8. PYTEST_ARGS

In `runner.sh`:

```bash
${PYTEST_ARGS}
```

means:

```text
Add any extra pytest options passed by the user at runtime.
```

Why this is useful:

```text
You can change pytest behavior without editing runner.sh or rebuilding the image.
```

Example 1 - pass report options:

```bash
PYTEST_ARGS="--html=reports/report.html --self-contained-html"
```

Then final command becomes:

```bash
pytest --grid --grid-url http://hub:4444/wd/hub --browser chrome -m smoke --html=reports/report.html --self-contained-html -v
```

Example 2 - run tests in parallel:

```bash
PYTEST_ARGS="-n 2"
```

Then final command becomes:

```bash
pytest --grid --grid-url http://hub:4444/wd/hub --browser chrome -m smoke -n 2 -v
```

Example 3 - run tests matching a name:

```bash
PYTEST_ARGS="-k login"
```

Then final command becomes:

```bash
pytest --grid --grid-url http://hub:4444/wd/hub --browser chrome -m smoke -k login -v
```

Where can `PYTEST_ARGS` be passed from?

Docker run:

```bash
docker run --rm -e PYTEST_ARGS="-m smoke --html=reports/report.html" python-selenium
```

Docker Compose:

```yaml
environment:
  - PYTEST_ARGS=--html=reports/report.html --self-contained-html
```

Shell before compose:

```bash
PYTEST_ARGS="-n 2" docker compose up --build
```

In this Dockerfile, default value is empty:

```dockerfile
ENV PYTEST_ARGS=""
```

So if user does not pass anything, runner still works normally.

Important:

```text
TEST_SUITE is for common marker selection like smoke/login/regression.
PYTEST_ARGS is for any extra pytest option like reports, parallel run, keyword filter, reruns, etc.
```

## 9. This Syntax: ${TEST_SUITE:+-m ${TEST_SUITE}}

```bash
${TEST_SUITE:+-m ${TEST_SUITE}}
```

Meaning:

```text
If TEST_SUITE has value, add pytest marker command.
If TEST_SUITE is empty, add nothing.
```

Examples:

```text
TEST_SUITE=smoke      -> -m smoke
TEST_SUITE=login      -> -m login
TEST_SUITE=regression -> -m regression
TEST_SUITE empty      -> nothing
```

So the same `runner.sh` can run:

```text
all tests
smoke tests
login tests
regression tests
```

based on environment variable.

## 10. Why Local Selenium Grid Section Did Not Use runner.sh

In:

```text
C:\docker_test\workspace\04-selenium-grid\03-max-sessions\docker-compose.yaml
```

compose starts only:

```text
hub container
chrome node container
firefox node container
```

There is no test container.

You run tests manually from your local machine:

```bash
pytest --grid --grid-url http://localhost:4444/wd/hub -v
```

Manual flow:

```text
1. docker compose up
2. open http://localhost:4444/ui
3. confirm Grid UI/nodes are ready
4. run pytest from local terminal
```

So in this case:

```text
human waits/checks Grid readiness
```

That is why `runner.sh` was not required there.

## 11. Why Dockerized Section Uses runner.sh

In `05-dockerize`, compose starts:

```text
hub container
chrome/firefox node container
test container
```

When you run:

```bash
docker compose up
```

everything starts automatically.

The test container may start before Hub is ready.

So `runner.sh` is used:

```text
script waits/checks Grid readiness
```

Comparison:

```text
04-selenium-grid -> human waits, then runs pytest locally
05-dockerize     -> runner.sh waits, then runs pytest inside test container
```

## 12. Final One-Line Summary

```text
runner.sh is a small safety script that prints runtime values, waits until Selenium Hub is really ready, and then runs the correct pytest command against the Grid.
```
