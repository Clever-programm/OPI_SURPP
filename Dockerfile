FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

WORKDIR /app

COPY backend/pyproject.toml backend/poetry.lock ./

RUN poetry install --only main

COPY backend ./backend

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]