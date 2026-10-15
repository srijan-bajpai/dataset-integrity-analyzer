FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DIA_ENV=production

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
COPY requirements-v2.txt ./requirements-v2.txt
RUN pip install --no-cache-dir -r requirements-v2.txt
COPY . .
RUN mkdir -p /data
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn dia.api.main:app --host 0.0.0.0 --port 8000"]
