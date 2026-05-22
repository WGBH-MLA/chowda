#!/bin/bash

gunicorn chowda.app:app \
    -b 0.0.0.0:8000 \
    -w 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --forwarded-allow-ips='*' \
    --proxy-protocol v2 \
    --proxy-allow-from='*' \
    --access-logfile - \
    --error-logfile -
