FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/sources.list.d/github-cli.list > /dev/null \
    && apt-get update \
    && apt-get install -y gh \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

RUN useradd -m -s /bin/bash osbot
USER osbot

VOLUME ["/app/state"]

HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
    CMD python -c "from pathlib import Path; import sys; p=Path('/app/state/heartbeat'); sys.exit(0 if p.exists() and (import_time:=__import__('time')) and (import_time.time() - p.stat().st_mtime < 900) else 1)" || exit 1

ENTRYPOINT ["python", "-m", "osbot"]
