###########################
# 'base' build stage, common to all build stages
###########################
FROM python as base
# Set working dir to /app, where all Chowda code lives.
WORKDIR /app
# Install uvicorn (ASGI web server) and poetry (dependency manager) using pip.
RUN pip install -U pip uvicorn poetry
# Copy app code to container
COPY pyproject.toml poetry.lock README.md ./

###########################
# 'dev' build stage
###########################
FROM base as dev

# Install dev dependencies with poetry
RUN poetry install -n --with dev
# Start dev server.
CMD poetry run uvicorn chowda:app --host 0.0.0.0 --reload


###########################
# 'test' build stage
###########################
FROM dev as test
# Install test requiremens with poetry
RUN poetry install -n --with test
# Copy the test code
COPY tests tests
# Run the tests
CMD poetry run pytest -v -n auto


###########################
# 'locust' build stage for load testing
############################
FROM test as locust
RUN pip install locust
CMD poetry run locust


###########################
# 'production' build stage
############################
FROM base as production
RUN poetry install --without dev,test
CMD poetry run uvicorn chowda:app --host 0.0.0.0
