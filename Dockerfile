FROM python

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY ./chowda /app/chowda

CMD uvicorn chowda.app:app --host 0.0.0.0