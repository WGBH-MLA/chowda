#!/bin/bash

uv run uvicorn chowda.app:app \
    --host 0.0.0.0 \
    --reload \
    --log-level debug
