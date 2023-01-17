FROM python

WORKDIR /app

# RUN pip install -U pip setuptools poetry

# COPY . .

# RUN poetry install

COPY requirements.txt .
RUN pip install -U pip uvicorn

RUN pip install -r requirements.txt

CMD uvicorn main:app --host 0.0.0.0 --reload