# Base stage - common to all builds
FROM python as base

WORKDIR /app

# Dev stage
# Copy requirements.txt run pip to install them.
# Expects:
# * bind mount of project root dir to containers /app dir.
# * port forwarding to container port 8000
# Start dev server.
FROM base as dev
COPY requirements.txt .
RUN pip install -U pip uvicorn
RUN pip install -r requirements.txt
CMD uvicorn main:app --host 0.0.0.0 --reload

FROM dev as tests
CMD pytest
