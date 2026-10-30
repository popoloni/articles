# Optional offline unit-test smoke; override CMD with validate.py for the full reader run.
# For byte-pinned builds, pass --build-arg PYTHON_IMAGE=python@sha256:<verified digest>.
ARG PYTHON_IMAGE=python:3.11-slim
FROM ${PYTHON_IMAGE}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /work
COPY . /work
USER 10001:10001
CMD ["python", "-m", "unittest", "discover", "-s", "tests", "-v"]
