# ---------- build stage ----------
FROM python:3.12-slim AS builder

WORKDIR /app

# Install deps into an isolated prefix so we can copy them cleanly
RUN pip install --no-cache-dir \
    "langgraph>=0.2.0" \
    "anthropic>=0.95.0" \
    "httpx>=0.28.1" \
    "pydantic>=2.13.0" \
    "python-dotenv>=1.2.2" \
    "structlog>=25.5.0"

# ---------- runtime stage ----------
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source — prompts directory must travel with src/
COPY src/ ./src/
COPY main.py ./

# src/ is on the Python path so imports work without sys.path hacks
ENV PYTHONPATH=/app/src
# Structured JSON logs in CI; set LOG_FORMAT=text locally
ENV LOG_FORMAT=json

ENTRYPOINT ["python", "main.py"]
