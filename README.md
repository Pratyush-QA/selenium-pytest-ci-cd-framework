# Selenium Pytest CI/CD Framework

A production-style, end-to-end test automation framework built with **Python + Selenium + pytest**, fully containerised with **Docker**, orchestrated with **Docker Compose**, and integrated into a **Jenkins CI/CD pipeline** with **AWS EC2** execution. This project mirrors how real QA teams run large-scale browser test automation in enterprise environments.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Test Framework | pytest |
| Browser Automation | Selenium WebDriver 4.x |
| Containerisation | Docker + Docker Compose |
| Browser Grid | Selenium Grid 4 (Hub + Node architecture) |
| CI/CD | Jenkins (declarative pipelines) |
| Cloud Execution | AWS EC2 as Jenkins agent |
| Image Registry | Docker Hub |
| Reporting | pytest-html |

---

## Project Structure

```
selenium-pytest-ci-cd-framework/
│
├── 01-docker/                        # Docker fundamentals
│   ├── Running Selenium tests inside a Docker container
│   └── Dockerfile basics, image build & run
│
├── 02-docker-compose/                # Multi-container orchestration
│   └── docker-compose.yaml for Grid + test services
│
├── 03-automation-frameworks/         # Standalone pytest framework (no Docker)
│   └── ui-automation-framework/
│       ├── src/  (driver, config, pages)
│       └── tests/ (smoke, regression)
│
├── 04-selenium-grid/                 # Selenium Grid integration
│   ├── docker-compose Grid setup (hub + chrome + firefox)
│   └── ui-automation-framework connected to remote Grid
│
├── 05-dockerize/                     # Fully dockerised framework (final project)
│   └── python-selenium/
│       ├── Dockerfile                # Multi-stage: build + run
│       ├── runner.sh                 # Entrypoint: runs pytest by TEST_SUITE env var
│       ├── requirements.txt
│       ├── src/
│       │   ├── driver/               # WebDriver factory (remote Grid support)
│       │   ├── config/               # URL, timeout, browser config
│       │   └── pages/                # Page Object Model (Login, Home, etc.)
│       └── tests/
│           ├── smoke/                # Fast sanity checks
│           └── regression/           # Full regression suite
│
├── 06-jenkins-ci-cd/                 # Jenkins pipeline progression
│   ├── 01-jenkins/                   # Jenkins setup & basics
│   ├── 02-simple-pipeline/           # Hello world Jenkinsfile
│   ├── 03-agent-label/               # Node label routing
│   ├── 04-env-variable/              # ENV vars in pipelines
│   ├── 05-run-container/             # Running Docker inside Jenkins
│   ├── 06-docker-agent/              # Docker container as Jenkins agent
│   ├── 07-image-builder-approach-1/  # Build + push image (bat commands)
│   ├── 08-image-builder-approach-2/  # Build + push (docker plugin)
│   ├── 09-runner-approach-1/         # Full pipeline: build→push→grid→test
│   │   ├── Jenkinsfile
│   │   ├── grid.yaml
│   │   └── test-suites.yaml
│   ├── 10-runner-approach-2/         # Runner with improvements
│   ├── 11-sample-ci-cd/              # Trigger downstream runner from CI pipeline
│   ├── 12-failure-handling/          # catchError: UNSTABLE vs FAILURE separation
│   └── 13-image-builder-approach-3/  # Docker agent per stage (no local installs)
│
└── 07-aws/                           # AWS EC2 cloud execution
    ├── 01-grid-and-test-suites/      # Combined compose for EC2
    └── 02-aws-runner/
        ├── Jenkinsfile               # agent { label 'EC2' }
        ├── grid.yaml                 # Hub + browser nodes (replicas: 0)
        ├── test-suites.yaml          # Test containers (external network)
        └── .env                      # SE_EVENT_BUS_HOST settings
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Jenkins Master                            │
│                (triggers pipelines)                          │
└────────────┬────────────────────────┬───────────────────────┘
             │                        │
    ┌────────▼────────┐      ┌────────▼────────┐
    │  Local Agent    │      │   AWS EC2 Agent │
    │  (Node1 label)  │      │   (EC2 label)   │
    └────────┬────────┘      └────────┬────────┘
             │                        │
    ┌────────▼────────────────────────▼────────┐
    │            Docker Compose                 │
    │  ┌──────────┐  ┌──────────┐              │
    │  │ selenium │  │  chrome  │  selenium-   │
    │  │   hub   │  │   node   │  grid network │
    │  └────┬─────┘  └──────────┘              │
    │       │                                   │
    │  ┌────▼──────────────────┐               │
    │  │  python-selenium:latest│ (Docker Hub)  │
    │  │  smoke-tests          │               │
    │  │  regression-tests     │               │
    │  └───────────────────────┘               │
    └───────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Page Object Model (POM)
All page interactions are encapsulated in `src/pages/`. Tests only call page methods — no raw Selenium calls in test files. This makes tests readable and maintenance easy.

### 2. Docker Image Layer Caching
```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt   # ← cached unless requirements.txt changes
COPY . .                              # ← only this layer rebuilds on code change
```
`requirements.txt` is copied first so pip install is cached on every code-only change — faster builds.

### 3. Two-Pipeline Architecture (CI/CD Split)
- **Image Builder pipeline** — builds and pushes `python-selenium:latest` to Docker Hub when code changes
- **Runner pipeline** — pulls latest image from Hub, starts Grid, runs tests
- This separates build concerns from execution concerns, matching real team workflows

### 4. Dynamic Browser Selection
```groovy
parameters { choice(choices: ['chrome', 'firefox'], name: 'BROWSER') }
```
```bash
docker-compose up --scale ${BROWSER}=1 -d
```
Only the selected browser node starts — no wasted container resources.

### 5. UNSTABLE vs FAILURE Separation
```groovy
catchError(buildResult: 'UNSTABLE', stageResult: 'UNSTABLE') {
    // test execution
}
```
Test failures → yellow (UNSTABLE). Infrastructure failures → red (FAILURE). Teams can distinguish flaky tests from broken pipelines.

### 6. AWS EC2 as Jenkins Agent
All test execution happens on EC2, not the developer's laptop. The laptop only views Jenkins UI. EC2 can be stopped after runs to save cost, or scaled out with more instances for parallel capacity.

---

## How to Run

### Local — Standalone (no Docker)
```bash
cd 03-automation-frameworks/ui-automation-framework
pip install -r requirements.txt
pytest tests/smoke/ --html=reports/report.html
```

### Local — Dockerised with Grid
```bash
cd 05-dockerize/python-selenium

# Start Selenium Grid
docker-compose -f docker-compose.yml up -d

# Run smoke tests (chrome)
docker-compose run -e BROWSER=chrome -e TEST_SUITE=smoke python-selenium sh runner.sh

# Tear down
docker-compose down
```

### Jenkins Pipeline (full CI/CD)
1. Configure Jenkins with `dockerhub-creds` credential (System → Global scope)
2. Create a Pipeline job pointing to this repo
3. Set Jenkinsfile path: `06-jenkins-ci-cd/09-runner-approach-1/Jenkinsfile`
4. Run — pipeline builds image → pushes to Hub → starts Grid → executes tests

---

## Jenkins Pipeline Flow (09-runner-approach-1)

```
Checkout → Build Image → Push to Hub → Start Grid → Run Tests → Teardown
```

```groovy
stage('Start Grid') {
    steps {
        bat "docker-compose -f 06-jenkins-ci-cd/09-runner-approach-1/grid.yaml up -d"
    }
}
stage('Run Tests') {
    steps {
        bat "docker-compose -f 06-jenkins-ci-cd/09-runner-approach-1/test-suites.yaml up --pull=always"
    }
}
```

---

## Interview Talking Points

- **Why Docker for test automation?** Eliminates "works on my machine" — same container runs on laptop, Jenkins agent, and EC2 with identical results.
- **Why Selenium Grid?** Enables parallel execution across browsers. Hub distributes sessions; nodes run them. Scales horizontally by adding node containers.
- **Why --pull=always?** Ensures the runner always uses the freshly built image from Hub, not a stale cached layer from a previous run.
- **Why split Image Builder and Runner pipelines?** Matches real teams: dev pushes code → image builder triggers on merge → runner triggers on schedule or demand. Clear separation of concerns.
- **Why EC2 as agent instead of local?** Moves resource consumption (RAM, CPU, Docker) off the developer's machine. EC2 is always-on, scalable, and cost-controllable (start/stop as needed).
- **How does the network work?** Grid and test containers join the same Docker bridge network (`selenium-grid`). Test containers reach the hub using the service name `hub` — no IP addresses needed.

---

## Prerequisites

- Docker Desktop (Linux containers mode)
- Python 3.11+
- Jenkins (with Docker plugin, Pipeline plugin)
- Docker Hub account with Personal Access Token

---

## Author

**Pratyush Jindal** — SDET  
[GitHub](https://github.com/Pratyush-QA) | [Docker Hub](https://hub.docker.com/u/pratyushjindal123)
