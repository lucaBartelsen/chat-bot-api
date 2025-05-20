# File: Dockerfile (updated)
# Path: fanfix-api/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install prisma CLI globally
RUN pip install prisma

# Create Prisma cache directory with proper permissions
RUN mkdir -p /app/.cache/prisma-python && chmod -R 777 /app/.cache

# Set PRISMA_HOME_DIR to use this custom cache location
ENV PRISMA_HOME_DIR=/app/.cache/prisma-python

# Copy project files
COPY . .

# Grant permissions to the prisma package directory
RUN chmod -R 777 /usr/local/lib/python3.10/site-packages/prisma

# Generate Prisma client (as root)
RUN prisma generate

# Make the init script executable
COPY init-database.sh /init-database.sh
RUN chmod +x /init-database.sh

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app /init-database.sh /app/.cache
USER appuser

# Expose port
EXPOSE 8000

# Start the application with the init script
CMD ["/init-database.sh"]