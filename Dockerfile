# syntax=docker/dockerfile:1

FROM python:3.14-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r requirements.txt

COPY app ./app
COPY alembic.ini .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

RUN mkdir -p data/uploads

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
