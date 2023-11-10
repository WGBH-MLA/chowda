###########################
# 'base' build stage, common to all build stages
###########################
FROM python:3.11 as base

# Set working dir to /app, where all Chowda code lives.
WORKDIR /app
RUN pip install -U pip

# Copy app code to container
COPY pyproject.toml pdm.lock README.md ./
COPY chowda chowda

# Copy migration files
COPY alembic.ini ./
COPY migrations migrations


###########################
# 'dev' build stage
###########################
FROM base as dev
# Install PDM dependency manager
RUN pip install pdm
# Configure pdm to instal dependencies into ./__pypyackages__/
RUN pdm config python.use_venv false
# Configure python to use pep582 with local __pypyackages__
ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages/pdm/pep582
# Add local packages to $PATH
ENV PATH=$PATH:/app/__pypackages__/3.11/bin/

# Install dev dependencies with pdm
RUN pdm install -G dev
# Start dev server.
CMD uvicorn chowda.app:app --host 0.0.0.0 --reload --log-level debug


###########################
# 'test' build stage
###########################
FROM base as test
# Install test requiremens with poetry
# Copy the test code
COPY tests tests
# Install test dependencies
RUN pip install .[test]
# Run the tests
CMD pytest -v -n auto


###########################
# 'locust' build stage for load testing
############################
FROM test as locust
RUN pip install .[locust]
CMD poetry run locust


###########################
# 'production' build stage
############################
FROM base as production
RUN pip install pdm
RUN pdm install -G production

COPY static static
COPY templates templates
ENV CHOWDA_ENV=production

CMD gunicorn chowda.app:app -b 0.0.0.0:8000 -w 2 --worker-class uvicorn.workers.UvicornWorker
