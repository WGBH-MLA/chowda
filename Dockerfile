FROM python

WORKDIR /app

# RUN pip install -U pip setuptools poetry
RUN pip install -U pip uvicorn

COPY requirements.txt .
COPY main.py .

# RUN poetry install
RUN pip install -r requirements.txt

CMD uvicorn main:app --host 0.0.0.0 --reload