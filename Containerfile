# Use a multi-stage build to keep the final image size small
# Stage 1: Builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
# --frozen: Require uv.lock to be up-to-date
# --no-install-project: We only want dependencies in this layer
RUN uv sync --frozen --no-install-project

# Stage 2: Runner
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV FLASK_APP=src/run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Copy the application code
COPY src ./src
COPY pyproject.toml .

# Expose the port
EXPOSE 8000

# Run command
# 1. We don't need 'uv run' here because we put the venv in PATH
# 2. We are in /app, so code is in /app/src. 
# 3. Gunicorn needs to find the app factory.
#    Since FLASK_APP is src/run.py, we might want to run from there, 
#    OR we can just point gunicorn to src.app:create_app() if we set PYTHONPATH.
#    Easier: Set PYTHONPATH to /app/src or just cd into it.

# Let's use the explicit python path approach
ENV PYTHONPATH=/app/src

CMD ["gunicorn", "-w", "3", "--threads", "4", "--worker-class", "gthread", "--timeout", "60", "-b", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
