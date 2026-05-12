# 01 - Running Tests in Docker

Run the Python Selenium tests inside a Docker container — no local Chrome or Python install needed.

## What this demonstrates

- Build a Docker image that contains Python, Chrome, and your test code
- Run tests fully inside the container (headless)
- Mount output folders so reports and screenshots land on your machine

## Commands

```bash
# Build the image
docker build -t python-selenium ../python-selenium

# Run all tests
docker run --rm \
  -v $(pwd)/../python-selenium/reports:/app/reports \
  -v $(pwd)/../python-selenium/screenshots:/app/screenshots \
  python-selenium

# Run smoke tests only
docker run --rm \
  -e PYTEST_ARGS="-m smoke" \
  -v $(pwd)/../python-selenium/reports:/app/reports \
  python-selenium

# Run regression tests only
docker run --rm \
  -e PYTEST_ARGS="-m regression" \
  -v $(pwd)/../python-selenium/reports:/app/reports \
  python-selenium
```

## How it works

```
docker run python-selenium
    └─ Dockerfile CMD: pytest ${PYTEST_ARGS} --headless
         └─ Chrome runs headless inside the container
         └─ Results written to /app/reports (mounted to host)
```

The container exits when tests finish. Exit code 0 = all passed, non-zero = failures.
