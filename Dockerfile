# Imagen slim: build rápido, imagen final pequeña -> cold starts más cortos
# en Cloud Run (importante porque escala a 0 entre requests).
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY cv_data ./cv_data
COPY rules.md ./rules.md

# Cloud Run inyecta $PORT en runtime; default 8080 para correr local igual.
ENV PORT=8080
EXPOSE 8080

CMD exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
