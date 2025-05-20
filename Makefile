.PHONY: setup run test lint clean docker-build docker-run

# Project variables
PROJECT_NAME = fanfix-api
PYTHON = python3
PIP = pip
VENV = venv
UVICORN = uvicorn
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Default target
.DEFAULT_GOAL := help

# Help target
help:
	@echo "Available commands:"
	@echo "  setup          Setup development environment"
	@echo "  run            Run development server"
	@echo "  test           Run tests"
	@echo "  lint           Run linting"
	@echo "  clean          Clean build artifacts"
	@echo "  docker-build   Build Docker images"
	@echo "  docker-run     Run with Docker Compose"

# Setup development environment
setup:
	chmod +x ./setup.sh
	./setup.sh

# Run development server
run:
	$(UVICORN) main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest

# Run linting
lint:
	flake8 app
	black app --check

# Clean build artifacts
clean:
	rm -rf __pycache__
	rm -rf app/__pycache__
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Docker commands
docker-build:
	$(DOCKER_COMPOSE) build

docker-run:
	$(DOCKER_COMPOSE) up