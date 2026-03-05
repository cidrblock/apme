# Cache maintainer: gRPC server for pull-galaxy, pull-requirements, clone-org.
# Needs ansible-galaxy and git. Mount cache volume at /cache (read-write).
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir ansible-core

ENV APME_CACHE_MAINTAINER_LISTEN=0.0.0.0:50052
ENV APME_CACHE_ROOT=/cache
EXPOSE 50052

CMD ["apme-cache-maintainer"]
