.PHONY: help setup run test lint clean up down build build-nocache ps logs ssl restart shell-api shell-db

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

# Colors for better readability
YELLOW = \033[1;33m
GREEN = \033[0;32m
NC = \033[0m # No Color

# Help target
help:
	@echo "${GREEN}$(PROJECT_NAME)${NC} - Available commands:"
	@echo ""
	@echo "${YELLOW}Development Commands:${NC}"
	@echo "  ${GREEN}setup${NC}          - Setup development environment"
	@echo "  ${GREEN}run${NC}            - Run development server locally"
	@echo "  ${GREEN}test${NC}           - Run tests"
	@echo "  ${GREEN}lint${NC}           - Run linting"
	@echo ""
	@echo "${YELLOW}Docker Commands:${NC}"
	@echo "  ${GREEN}build${NC}          - Build Docker images"
	@echo "  ${GREEN}build-nocache${NC}  - Build Docker images without cache"
	@echo "  ${GREEN}up${NC}             - Start containers (in detached mode)"
	@echo "  ${GREEN}down${NC}           - Stop and remove containers"
	@echo "  ${GREEN}restart${NC}        - Restart all services"
	@echo "  ${GREEN}ps${NC}             - Show running containers"
	@echo "  ${GREEN}logs${NC}           - View logs from all containers"
	@echo "  ${GREEN}clean${NC}          - Remove all containers, images, and volumes"
	@echo ""
	@echo "${YELLOW}Shell Access:${NC}"
	@echo "  ${GREEN}shell-api${NC}      - Open shell in API container"
	@echo "  ${GREEN}shell-db${NC}       - Open shell in database container"

# Setup development environment
setup:
	@echo "${GREEN}Setting up development environment...${NC}"
	chmod +x ./setup.sh
	./setup.sh

# Run development server
run:
	@echo "${GREEN}Starting development server...${NC}"
	$(UVICORN) main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	@echo "${GREEN}Running tests...${NC}"
	pytest

# Run linting
lint:
	@echo "${GREEN}Running linters...${NC}"
	flake8 app
	black app --check

# Docker commands
build:
	@echo "${GREEN}Building Docker images...${NC}"
	$(DOCKER_COMPOSE) build

build-nocache:
	@echo "${GREEN}Building Docker images without cache...${NC}"
	$(DOCKER_COMPOSE) build --no-cache

up:
	@echo "${GREEN}Starting containers in detached mode...${NC}"
	$(DOCKER_COMPOSE) up -d

down:
	@echo "${GREEN}Stopping and removing containers...${NC}"
	$(DOCKER_COMPOSE) down

restart:
	@echo "${GREEN}Restarting all services...${NC}"
	$(DOCKER_COMPOSE) restart

ps:
	@echo "${GREEN}Showing running containers...${NC}"
	$(DOCKER_COMPOSE) ps

logs:
	@echo "${GREEN}Viewing logs from all containers...${NC}"
	$(DOCKER_COMPOSE) logs -f

# Clean Docker resources
clean:
	@echo "${GREEN}Removing all containers, images, and volumes...${NC}"
	$(DOCKER_COMPOSE) down -v
	$(DOCKER) system prune -af --volumes

# Shell access to containers
shell-api:
	@echo "${GREEN}Opening shell in API container...${NC}"
	$(DOCKER_COMPOSE) exec api /bin/bash

shell-db:
	@echo "${GREEN}Opening shell in database container...${NC}"
	$(DOCKER_COMPOSE) exec db psql -U postgres -d chatsassistant-db