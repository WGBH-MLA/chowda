###########################
# 'base' build stage, common to all build stages
###########################
FROM python:3.14-slim as base

# Set working dir to /app, where all Chowda code lives.
WORKDIR /app
RUN pip install uv

# Copy app code to container
COPY pyproject.toml uv.lock README.md ./
COPY chowda chowda

# Copy migration files
COPY alembic.ini ./
COPY migrations migrations


###########################
# 'dev' build stage
###########################
FROM base as dev
# Sync dependencies
RUN uv sync
# Start dev server.
CMD uv run uvicorn chowda.app:app --host 0.0.0.0 --reload --log-level debug


###########################
# 'test' build stage
###########################
FROM base as test
# Copy the test code
COPY tests tests
# Install test dependencies
RUN uv sync -G test
# Run the tests
CMD uv run pytest -v -n auto


###########################
# 'locust' build stage for load testing
############################
FROM test as locust
RUN uv sync --extra locust
CMD uv run locust


###########################
# 'base' build stage for production
############################
FROM base as build
RUN apt update && apt install -y gcc libpq-dev git

# Sync production dependencies and install them into a virtual environment
RUN uv sync --extra production --no-dev

###########################
# 'production' final production image
############################
FROM python:3.14-slim as production
WORKDIR /app

RUN apt update && apt install -y libpq-dev
RUN apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /app/ /app/
COPY templates templates
COPY static static

ENV CHOWDA_ENV=production
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD gunicorn chowda.app:app -b 0.0.0.0:8000 -w 2 --worker-class uvicorn.workers.UvicornWorker --forwarded-allow-ips='*' --proxy-protocol
