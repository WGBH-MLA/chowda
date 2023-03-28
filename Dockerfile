# Base stage - common to all builds
FROM python as base

RUN pip install -U pip uvicorn

WORKDIR /app

FROM base as dev
# Dev stage
# Copy pyproject.toml and run pip to install project.
# Expects:
# * bind mount of project root dir to containers /app dir.
# * port forwarding to container port 8000
# Start dev server.

COPY pyproject.toml poetry.lock README.md ./
COPY chowda chowda

RUN pip install .

CMD uvicorn chowda:app --host 0.0.0.0 --reload


FROM dev as test
# Test stage
# Steps:
#    Copy test requirements
#    Copy tests
#    Run tests

COPY requirements-test.txt .
RUN pip install -r requirements-test.txt

COPY tests tests

CMD pytest -v -n auto
