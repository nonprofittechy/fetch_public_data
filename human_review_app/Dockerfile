FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    REVIEW_CASES_PATH=/app/data/review_cases.json \
    REVIEW_TAXONOMY_PATH=/app/data/taxonomy.json \
    REVIEW_DB_PATH=/data/reviews.sqlite3 \
    COOKIE_SECURE=1

WORKDIR /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/*
COPY human_review_app/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY human_review_app/app.py ./app.py
COPY human_review_app/templates ./templates
COPY human_review_app/static ./static
COPY human_review_app/entrypoint.sh ./entrypoint.sh
COPY silver_labels/10_four_label_human_review/review_cases.json ./data/review_cases.json
COPY silver_labels/10_four_label_human_review/taxonomy.json ./data/taxonomy.json

RUN mkdir -p /data && chown -R 1000:1000 /app /data && chmod 755 /app/entrypoint.sh
EXPOSE 8080

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "60", "--access-logfile", "-", "app:app"]
