FROM mcr.microsoft.com/devcontainers/javascript-node:1-24-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends chromium ffmpeg \
    && rm -rf /var/lib/apt/lists/*
