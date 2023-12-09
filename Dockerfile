# Dockerfile

FROM python:3.8

WORKDIR /app

COPY req.txt .

RUN pip install --upgrade pip \
    && pip install -r req.txt

COPY . .

CMD ["python", "main.py"]
