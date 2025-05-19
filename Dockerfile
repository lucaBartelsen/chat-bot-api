# File: Dockerfile
# Path: fanfix-api/Dockerfile

FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install prisma CLI globally
RUN pip install prisma

# Copy project files
COPY . .

# Generate Prisma client
RUN prisma generate

# Make the init script executable
COPY init-database.sh /init-database.sh
RUN chmod +x /init-database.sh

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app /init-database.sh
USER appuser

# Expose port
EXPOSE 8000

# Start the application with the init script
CMD ["/init-database.sh"]