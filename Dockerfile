# Base stage - common to all builds
FROM python as base

# Install uvicorn (ASGI web server) and poetry (dependency manager) using pip.
# Poetry will be used to install app dependencies from pyproject.toml.
RUN pip install -U pip uvicorn poetry

# Set working directory to /app in the container. All Chowda code lives here.
WORKDIR /app
# Copy app code to container
COPY pyproject.toml poetry.lock README.md ./
COPY chowda chowda

###########################
# 'test' build stage
###########################
FROM base as dev
# Install dev dependencies with poetry
RUN poetry install --with dev
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
