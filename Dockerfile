FROM python
WORKDIR /app

RUN pip install -U pip uvicorn

COPY pyproject.toml poetry.lock README.md ./
COPY chowda chowda

RUN pip install .

CMD uvicorn chowda.app:app --host 0.0.0.0