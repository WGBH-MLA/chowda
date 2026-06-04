###########################
# 'base' build stage, common to all build stages
###########################
FROM python:3.14-slim AS base

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
FROM base AS dev
# Sync dependencies
RUN uv sync

# Start dev server.
COPY entrypoints/dev.sh .
CMD ["./dev.sh"]


###########################
# 'test' build stage
###########################
FROM base AS test
# Copy the test code
COPY tests tests
# Install test dependencies
RUN uv sync -G test

# Run the tests
COPY entrypoints/test.sh .
CMD ["./test.sh"]


###########################
# 'locust' build stage for load testing
############################
FROM test AS locust
RUN uv sync --extra locust

COPY entrypoints/locust.sh .
CMD ["./locust.sh"]


###########################
# 'base' build stage for production
############################
FROM base AS build
RUN apt update && apt install -y gcc libpq-dev git

# Sync production dependencies and install them into a virtual environment
RUN uv sync --extra production --no-dev

###########################
# 'production' final production image
############################
FROM python:3.14-slim AS production
WORKDIR /app

RUN apt update && apt install -y libpq-dev git
# RUN apt-get autoremove -y \
#     && apt-get clean -y \
#     && rm -rf /var/lib/apt/lists/*
COPY --from=build /app/ /app/
COPY templates templates
COPY static static
RUN pip install .[production]

ENV CHOWDA_ENV=production
# ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

COPY entrypoints/production.sh .

CMD ["./production.sh"]
