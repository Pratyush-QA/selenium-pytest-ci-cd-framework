# Section A - Dockerfile Notes

File explained:

```text
C:\docker_test\workspace\05-dockerize\python-selenium\Dockerfile
```

## 1. What This Dockerfile Does

This Dockerfile creates a Docker image for the Python Selenium framework.

The final image contains:

```text
Python
framework code
pytest dependencies
Chrome browser
Linux libraries needed by Chrome
runner.sh
output folders for reports/logs/screenshots
```

Simple idea:

```text
Dockerfile = recipe
Image      = prepared package
Container  = running copy of that image
```

The Dockerfile prepares the image. The container runs tests from that image.

## 2. Base Image

```dockerfile
FROM python:3.11-slim
```

This means:

```text
Start from a small Linux image that already has Python 3.11.
```

Important:

```text
This is not a Selenium Grid image.
This is the test runner image.
```

Because it is a slim image, it does not include Chrome and many Chrome-related Linux libraries. We install those manually later.

## 3. Labels

```dockerfile
LABEL description="Selenium + Pytest UI Automation Framework"
LABEL target="https://the-internet.herokuapp.com"
```

Labels are metadata stored inside the image.

They do not:

```text
install anything
run tests
change browser behavior
```

They help describe the image.

Example:

```text
description -> what this image is for
target      -> application/site under test
```

You can inspect labels using:

```bash
docker image inspect python-selenium
```

Interview answer:

```text
LABEL adds metadata to the Docker image. It is useful for documentation, tracking, and image inspection.
```

## 4. Environment Variables

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=ci \
    HEADLESS=true \
    PYTEST_ARGS="" \
    DISPLAY=:99
```

The first `ENV` is the Dockerfile keyword.

It means:

```text
Set default environment variables inside the image/container.
```

Line by line:

```text
PYTHONDONTWRITEBYTECODE=1 -> Python will not create .pyc/__pycache__ files
PYTHONUNBUFFERED=1        -> Python logs print immediately in Docker/CI
ENV=ci                    -> framework uses CI/container config
HEADLESS=true             -> browser should run without visible UI
PYTEST_ARGS=""            -> default extra pytest args are empty
DISPLAY=:99               -> virtual display value for Linux GUI tools
```

Do not confuse:

```dockerfile
ENV ENV=ci
```

First `ENV`:

```text
Dockerfile instruction
```

Second `ENV`:

```text
environment variable name used by framework
```

## 5. ENV vs WORKDIR

Environment variables are not set only inside one folder.

Example:

```dockerfile
WORKDIR /app
ENV HEADLESS=true
```

`WORKDIR` means:

```text
Default current folder is /app
```

`ENV` means:

```text
Set variable globally for processes running inside the container
```

So `HEADLESS=true` is available to commands running from `/app`, `/tmp`, or any other folder inside the container.

Simple difference:

```text
WORKDIR -> where commands run from
ENV     -> values commands can read
```

## 6. Environment Variable Levels

Environment variables can be set in multiple places.

### Dockerfile Level

```dockerfile
ENV HEADLESS=true
ENV PYTEST_ARGS=""
```

Meaning:

```text
Default values baked into the image.
```

### Docker Compose Level

```yaml
environment:
  - HUB_HOST=hub
  - BROWSER=chrome
  - TEST_SUITE=smoke
```

Meaning:

```text
Values passed when a specific service container starts.
```

Useful because the same image can behave differently for different services.

Example:

```text
smoke-tests -> BROWSER=chrome, TEST_SUITE=smoke
login-tests -> BROWSER=firefox, TEST_SUITE=login
```

### Host/CI Runtime Level

Example:

```bash
PYTEST_ARGS="-n 2" docker compose up --build
```

Meaning:

```text
User or CI passes value for this specific run.
```

Simple priority:

```text
Dockerfile ENV = default
Compose environment = overrides Dockerfile default
docker run -e / CI runtime value = runtime override
```

Best practice:

```text
Dockerfile -> safe defaults
Compose    -> service-specific values
Host/CI    -> values that change per run
```

## 7. Install Linux Packages and Chrome

Dockerfile section:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget \
        curl \
        gnupg \
        unzip \
        ca-certificates \
        fonts-liberation \
        libasound2 \
        libatk-bridge2.0-0 \
        libatk1.0-0 \
        libcups2 \
        libdbus-1-3 \
        libdrm2 \
        libgbm1 \
        libgtk-3-0 \
        libnspr4 \
        libnss3 \
        libxcomposite1 \
        libxdamage1 \
        libxfixes3 \
        libxkbcommon0 \
        libxrandr2 \
        xdg-utils \
        jq \
    && install -d -m 0755 /etc/apt/keyrings \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
       | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg \
    && chmod a+r /etc/apt/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

High-level meaning:

```text
Install helper tools, Chrome dependencies, Google Chrome, then clean cache.
```

### apt-get update

```dockerfile
apt-get update
```

Meaning:

```text
Refresh Linux package list.
```

### apt-get install

```dockerfile
apt-get install -y --no-install-recommends
```

Meaning:

```text
Install packages.
```

Options:

```text
-y                      -> automatically answer yes
--no-install-recommends -> install fewer extra packages, keep image smaller
```

## 8. Why curl and jq Are Installed

`runner.sh` uses `curl` and `jq`.

This command checks Selenium Hub readiness:

```bash
curl -s http://${HUB_HOST:-hub}:4444/status | jq -r .value.ready
```

Meaning:

```text
curl -> call Selenium Hub /status API
jq   -> read ready value from JSON response
```

Example Hub response:

```json
{
  "value": {
    "ready": true
  }
}
```

`jq -r .value.ready` extracts:

```text
true
```

So for Grid mode:

```text
curl and jq are required by runner.sh.
```

## 9. Why Chrome and Chrome Dependencies Are Installed

This is the most important doubt.

In Grid mode, browser runs in the node container:

```text
test container -> pytest code
hub container  -> routes WebDriver commands
node container -> actual Chrome/Firefox browser
```

So in pure Grid mode:

```text
Chrome is not required inside test container.
```

Then why install Chrome in this image?

Because this Dockerfile supports two use cases.

## 10. Use Case 1 - Run Tests Without Grid

Dockerfile has:

```dockerfile
CMD ["sh", "-c", "pytest ${PYTEST_ARGS} --headless"]
```

If we run:

```bash
docker run python-selenium
```

There is no Hub and no Chrome node.

Flow:

```text
test container
  -> pytest runs here
  -> Chrome also runs here
```

So Chrome is required inside the test container.

Good for:

```text
quick smoke test
simple CI job
small test suite
single-browser execution
easy setup/debugging
```

## 11. Use Case 2 - Run Tests With Selenium Grid

Compose can override Dockerfile `CMD`:

```yaml
command: sh runner.sh
```

Then `runner.sh` runs:

```bash
pytest --grid --grid-url http://hub:4444/wd/hub
```

Flow:

```text
test container
  -> pytest runs here
  -> sends WebDriver commands to Hub

hub container
  -> routes commands to browser node

chrome/firefox node container
  -> actual browser runs here
```

In this mode:

```text
Chrome inside the test image is not really used.
```

For pure Grid-only execution, the test image can be lighter:

```text
Python + framework code + dependencies + curl + jq
```

Chrome can be removed if this image will never run standalone tests.

## 12. When to Use Single Test Container vs Grid

### Single Test Container

Use when:

```text
You want simple execution
You run a small suite
You only need one browser
You want quick CI smoke validation
You do not need heavy parallel execution
```

Flow:

```text
test container = pytest + Chrome
```

### Selenium Grid

Use when:

```text
You need Chrome + Firefox
You need parallel execution
You need multiple browser sessions
You want browser infra separate from test code
You want scalable CI execution
```

Flow:

```text
test container = pytest only
hub container = routing
node containers = real browsers
```

Simple decision:

```text
Use single test container for simplicity.
Use Selenium Grid for scale, parallelism, and cross-browser execution.
```

## 13. Add Google Chrome Repository

```dockerfile
install -d -m 0755 /etc/apt/keyrings
```

Meaning:

```text
Create the folder where apt repository keys are stored.
```

Then:

```dockerfile
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub \
   | gpg --dearmor -o /etc/apt/keyrings/google-chrome.gpg
```

Meaning:

```text
Download Google's signing key and store it as a keyring file.
```

Then:

```dockerfile
chmod a+r /etc/apt/keyrings/google-chrome.gpg
```

Meaning:

```text
Allow apt to read the keyring file.
```

Then:

```dockerfile
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
   > /etc/apt/sources.list.d/google-chrome.list
```

Meaning:

```text
Tell apt where to download google-chrome-stable from and which key should verify it.
```

Why not `apt-key add`?

```text
apt-key is deprecated and is missing in newer slim Debian images.
The keyring + signed-by approach is the modern replacement.
```

Then:

```dockerfile
apt-get update
apt-get install -y --no-install-recommends google-chrome-stable
```

Meaning:

```text
Refresh package list again and install Chrome.
```

## 14. Cleanup

```dockerfile
apt-get clean
rm -rf /var/lib/apt/lists/*
```

Meaning:

```text
Remove apt cache and temporary package list files.
```

Why?

```text
To reduce Docker image size.
```

## 15. WORKDIR

```dockerfile
WORKDIR /app
```

Meaning:

```text
Set /app as the default working directory inside image/container.
```

After this, commands run from `/app` by default.

So:

```dockerfile
COPY requirements.txt .
```

means:

```text
Copy requirements.txt into /app
```

And:

```dockerfile
COPY . .
```

means:

```text
Copy project into /app
```

## 16. Copy requirements.txt and Install Python Dependencies

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
```

First:

```dockerfile
COPY requirements.txt .
```

Meaning:

```text
Copy requirements.txt from project folder into /app inside image.
```

Then:

```dockerfile
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
```

Meaning:

```text
Upgrade pip.
Install all Python packages listed in requirements.txt.
```

Example dependencies:

```text
selenium
pytest
pytest-html
allure-pytest
```

`--no-cache-dir` means:

```text
Do not keep pip download cache, so image stays smaller.
```

`&&` means:

```text
Run second command only if first command succeeds.
```

## 17. Why Copy requirements.txt Before Full Project

This is done for Docker build cache.

Good pattern:

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

Why?

```text
Dependencies change rarely.
Test code changes often.
```

If only test code changes:

```text
pip install layer can be reused from Docker cache.
```

This makes rebuilds faster.

Important:

```text
This cache is image build cache, not container cache.
```

`docker compose down` removes containers/networks, but image/cache usually remains.

So next image build can still reuse the dependency layer.

## 18. Copy Full Project

```dockerfile
COPY . .
```

Meaning:

```text
Copy everything from the current project folder into /app inside image.
```

Example:

```text
Host:
python-selenium/
  runner.sh
  tests/
  src/
  config/

Image:
/app/
  runner.sh
  tests/
  src/
  config/
```

## 19. chmod +x runner.sh

```dockerfile
RUN chmod +x runner.sh
```

Meaning:

```text
Add execute permission to runner.sh.
```

It does not run `runner.sh`.

It only makes this possible:

```bash
./runner.sh
```

Comparison:

```text
sh runner.sh     -> does not strictly need +x because sh executes the file
./runner.sh      -> needs +x because script itself is executed
python test.py   -> test.py does not need +x because python executes the file
```

Why keep `chmod +x`?

```text
Good practice. It allows direct script execution if needed.
```

## 20. Create Output Folders

```dockerfile
mkdir -p screenshots reports logs allure-results
```

Meaning:

```text
Create folders inside the image/container for test outputs.
```

Folders:

```text
screenshots     -> failed test screenshots
reports         -> HTML reports
logs            -> framework logs
allure-results  -> Allure result files
```

`-p` means:

```text
Do not fail if folder already exists.
Create parent folders if needed.
```

## 21. Combined RUN chmod and mkdir

Dockerfile has:

```dockerfile
RUN chmod +x runner.sh \
    && mkdir -p screenshots reports logs allure-results
```

`\` means:

```text
Continue command on next line.
```

`&&` means:

```text
Run mkdir only if chmod succeeds.
```

Same as one line:

```dockerfile
RUN chmod +x runner.sh && mkdir -p screenshots reports logs allure-results
```

## 22. CMD

```dockerfile
CMD ["sh", "-c", "pytest ${PYTEST_ARGS} --headless"]
```

Meaning:

```text
Default command when container starts.
```

Breakdown:

```text
CMD        -> default command for container startup
sh         -> shell program
-c         -> tells shell to run the next string as a command
pytest ... -> actual command we want to run
```

Why use `sh -c`?

```text
Because ${PYTEST_ARGS} is an environment variable.
The shell expands it before running pytest.
```

Without shell expansion, Docker may pass `${PYTEST_ARGS}` as plain text instead of replacing it with the actual runtime value.

If you run:

```bash
docker run python-selenium
```

then container runs:

```bash
pytest ${PYTEST_ARGS} --headless
```

If `PYTEST_ARGS` is empty:

```bash
pytest --headless
```

If user passes:

```bash
docker run -e PYTEST_ARGS="-m smoke" python-selenium
```

then command becomes:

```bash
pytest -m smoke --headless
```

Important:

```text
CMD can be overridden by docker run command or docker-compose command.
```

Example in compose:

```yaml
command: sh runner.sh
```

This overrides Dockerfile `CMD`.

## 23. Dockerfile CMD vs docker-compose command

Dockerfile:

```dockerfile
CMD ["sh", "-c", "pytest ${PYTEST_ARGS} --headless"]
```

Used for:

```text
standalone container test execution
```

Flow:

```text
test container starts
Dockerfile CMD runs
pytest runs directly
Chrome runs inside same test container
no Selenium Grid is used
```

Example:

```bash
docker run python-selenium
```

Compose:

```yaml
command: sh runner.sh
```

Used for:

```text
Grid execution
wait for Hub first, then run pytest
```

Flow:

```text
test container starts
compose command overrides Dockerfile CMD
runner.sh runs
runner.sh waits for Selenium Hub
runner.sh starts pytest with --grid
browser runs inside Chrome/Firefox node container
```

Example:

```bash
docker compose up --build
```

Simple:

```text
Dockerfile CMD        -> direct container test run
docker-compose command -> Grid test run through runner.sh
```

Important:

```text
In both cases, pytest/test cases start from the test container.
The difference is where the browser runs.
```

```text
Standalone mode -> browser runs inside test container
Grid mode       -> browser runs inside browser node container
```

## 24. What Happens During docker build

Command:

```bash
docker build -t python-selenium .
```

Internal flow:

```text
1. Docker reads Dockerfile
2. Sends current folder as build context
3. Runs Dockerfile instructions one by one
4. Creates image layers
5. Saves final image locally as python-selenium:latest
```

Important:

```text
docker build prepares image.
docker run starts container from image.
```

`docker build` does not run tests. It only creates the ready-to-run automation image.

## 25. Final One-Line Summary

```text
This Dockerfile builds a reusable Selenium + Pytest test-runner image that can run tests either standalone with Chrome inside the test container or against Selenium Grid where browsers run in separate node containers.
```
