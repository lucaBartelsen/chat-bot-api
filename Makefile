# File: Makefile
# Path: fanfix-api/Makefile

.PHONY: setup install dev test lint format docker-build docker-up docker-down migrate generate-prisma db-init clean

# Environment setup
setup: install db-init generate-prisma

# Install dependencies
install:
	pip install -r requirements.txt

# Run development server
dev:
	uvicorn main:app --reload

# Run tests
test:
	pytest

# Lint code
lint:
	flake8 app tests
	mypy app

# Format code
format:
	black app tests

# Build Docker image
docker-build:
	docker-compose build

# Start Docker containers
docker-up:
	docker-compose up -d

# Stop Docker containers
docker-down:
	docker-compose down

# Run database migrations
migrate:
	@echo "Running migration script..."
	psql -U postgres -d fanfix_db -f migrations/0001_initial.sql

# Generate Prisma client
generate-prisma:
	prisma generate

# Initialize database with pgvector extension
db-init:
	@echo "Creating database..."
	createdb -U postgres fanfix_db || true
	@echo "Installing pgvector extension..."
	psql -U postgres -d fanfix_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Clean up generated files
clean:
	rm -rf __pycache__
	rm -rf app/__pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache