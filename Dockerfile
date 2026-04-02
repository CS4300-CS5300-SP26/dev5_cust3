# ── Stage 1: Builder ────────────────────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Production ─────────────────────────────────────────────
FROM python:3.13-slim AS production

RUN useradd -m -r knowledgeUser && mkdir /app && chown -R knowledgeUser /app

COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

WORKDIR /app

COPY --chown=knowledgeUser:knowledgeUser . .

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Only exists at build time, never stored in the image
ARG SECRET_KEY=build-time-placeholder
RUN SECRET_KEY=${SECRET_KEY} python ./knowledge_map/manage.py collectstatic --noinput

USER knowledgeUser

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "knowledge_map.wsgi:application"]