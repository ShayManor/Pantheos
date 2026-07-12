# syntax=docker/dockerfile:1
# One image: builds the React frontend, then serves it + the Flask API from
# gunicorn. The API talks to the Hermes agent on the host via SSH (openssh-client).

# ---- Stage 1: build the frontend (Vite -> /fe/dist) ----
FROM node:22-slim AS frontend
WORKDIR /fe
COPY pantheos/package.json pantheos/package-lock.json ./
RUN npm ci
COPY pantheos/ ./
RUN npm run build

# ---- Stage 2: python runtime serving API + built frontend ----
FROM python:3.12-slim AS app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
# openssh-client: the app reaches the host's `hermes` via `ssh minipc ... hermes acp`
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY pantheos-api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY pantheos-api/ ./
COPY --from=frontend /fe/dist ./frontend
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENV PANTHEOS_FRONTEND_DIST=/app/frontend
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
# gthread workers so a long-lived SSE stream never blocks other requests.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "gthread", \
     "--workers", "2", "--threads", "8", "--timeout", "300", "wsgi:app"]
