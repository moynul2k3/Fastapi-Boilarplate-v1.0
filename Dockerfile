# Stage 1: Builder
FROM python:3.12-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmariadb-dev-compat \
    libmariadb-dev \
    default-mysql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel --no-cache-dir --no-deps -r requirements.txt -w /wheels

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmariadb-dev-compat \
    libmariadb-dev \
    default-mysql-client \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

COPY . .

RUN mkdir -p /app/media

# Add non-root user
RUN useradd -m fastapiuser
RUN chown -R fastapiuser:fastapiuser /app

# Copy start.sh
COPY start.sh /start.sh
RUN chmod +x /start.sh

USER fastapiuser

EXPOSE 8000

# Start the app with startup script
CMD ["/start.sh"]

# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
