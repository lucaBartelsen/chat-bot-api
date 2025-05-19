# File: Makefile
# Path: fanfix-api/Makefile

# Variables
DOCKER_COMPOSE = docker-compose
IMAGE_NAME = fanfix-api
TAG = latest
ENV_FILE = .env

# Colors for terminal output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m  # No Color

.PHONY: help setup build up down restart logs ps clean \
        db-shell db-backup db-restore \
        ssl-check create-admin format lint test

# Help command
help:
	@echo "${GREEN}FanFix ChatAssist API Makefile Commands:${NC}"
	@echo ""
	@echo "${YELLOW}Setup and Building:${NC}"
	@echo "  ${GREEN}setup${NC}        - Create necessary directories and files"
	@echo "  ${GREEN}build${NC}        - Build containers"
	@echo "  ${GREEN}build-nocache${NC} - Build containers without cache"
	@echo ""
	@echo "${YELLOW}Container Management:${NC}"
	@echo "  ${GREEN}up${NC}           - Start all containers"
	@echo "  ${GREEN}down${NC}         - Stop and remove containers"
	@echo "  ${GREEN}restart${NC}      - Restart all containers"
	@echo "  ${GREEN}logs${NC}         - View all container logs"
	@echo "  ${GREEN}logs-api${NC}     - View API container logs"
	@echo "  ${GREEN}logs-db${NC}      - View database container logs"
	@echo "  ${GREEN}logs-nginx${NC}   - View nginx container logs"
	@echo "  ${GREEN}ps${NC}           - List all containers"
	@echo ""
	@echo "${YELLOW}Database Operations:${NC}"
	@echo "  ${GREEN}db-shell${NC}     - Open a PostgreSQL shell"
	@echo "  ${GREEN}db-backup${NC}    - Backup database to backup.sql"
	@echo "  ${GREEN}db-restore${NC}   - Restore database from backup.sql"
	@echo ""
	@echo "${YELLOW}Utility Commands:${NC}"
	@echo "  ${GREEN}ssl-check${NC}    - Check SSL certificates for Cloudflare"
	@echo "  ${GREEN}clean${NC}        - Remove all containers and volumes"
	@echo "  ${GREEN}create-admin${NC} - Create an admin user"
	@echo "  ${GREEN}format${NC}       - Format code with Black"
	@echo "  ${GREEN}lint${NC}         - Lint code with flake8"
	@echo "  ${GREEN}test${NC}         - Run tests"

# Setup command
setup:
	@echo "${GREEN}Setting up project structure...${NC}"
	@mkdir -p nginx/conf.d nginx/ssl nginx/www
	@[ -f .env ] || cp .env.example .env
	@echo "${YELLOW}Remember to update your .env file with actual values!${NC}"
	@echo "${YELLOW}Place your Cloudflare SSL certificates in the nginx/ssl directory.${NC}"

# Build Docker images
build:
	@echo "${GREEN}Building Docker images...${NC}"
	@$(DOCKER_COMPOSE) build

# Build without cache
build-nocache:
	@echo "${GREEN}Building Docker images without cache...${NC}"
	@$(DOCKER_COMPOSE) build --no-cache

# Start containers
up:
	@echo "${GREEN}Starting containers...${NC}"
	@$(DOCKER_COMPOSE) up -d
	@echo "${GREEN}Services started. API available at:${NC}"
	@echo "  - Local: ${YELLOW}http://localhost:8000${NC}"
	@echo "  - Production: ${YELLOW}https://chatsassistant.com${NC}"
	@echo "  - API Docs: ${YELLOW}https://chatsassistant.com/docs${NC}"

# Stop and remove containers
down:
	@echo "${GREEN}Stopping containers...${NC}"
	@$(DOCKER_COMPOSE) down

# Restart containers
restart:
	@echo "${GREEN}Restarting containers...${NC}"
	@$(DOCKER_COMPOSE) restart

# View logs
logs:
	@echo "${GREEN}Viewing logs...${NC}"
	@$(DOCKER_COMPOSE) logs -f

# View API logs
logs-api:
	@echo "${GREEN}Viewing API logs...${NC}"
	@$(DOCKER_COMPOSE) logs -f api

# View database logs
logs-db:
	@echo "${GREEN}Viewing database logs...${NC}"
	@$(DOCKER_COMPOSE) logs -f db

# View nginx logs
logs-nginx:
	@echo "${GREEN}Viewing nginx logs...${NC}"
	@$(DOCKER_COMPOSE) logs -f nginx

# List containers
ps:
	@echo "${GREEN}Listing containers...${NC}"
	@$(DOCKER_COMPOSE) ps

# Open a PostgreSQL shell
db-shell:
	@echo "${GREEN}Opening PostgreSQL shell...${NC}"
	@$(DOCKER_COMPOSE) exec db psql -U postgres -d fanfix_db

# Backup database
db-backup:
	@echo "${GREEN}Backing up database to backup.sql...${NC}"
	@$(DOCKER_COMPOSE) exec db pg_dump -U postgres fanfix_db > backup.sql
	@echo "${GREEN}Backup completed: backup.sql${NC}"

# Restore database
db-restore:
	@echo "${GREEN}Restoring database from backup.sql...${NC}"
	@cat backup.sql | $(DOCKER_COMPOSE) exec -T db psql -U postgres -d fanfix_db
	@echo "${GREEN}Restore completed${NC}"

# Check SSL certificates
ssl-check:
	@if [ -f nginx/ssl/origin-certificate.pem ] && [ -f nginx/ssl/private-key.pem ]; then \
		echo "${GREEN}SSL certificates found:${NC}"; \
		echo "  - origin-certificate.pem"; \
		echo "  - private-key.pem"; \
		echo "${YELLOW}Checking certificate details:${NC}"; \
		openssl x509 -in nginx/ssl/origin-certificate.pem -text -noout | grep -E 'Subject:|Issuer:|Not Before:|Not After :'; \
	else \
		echo "${RED}SSL certificates not found!${NC}"; \
		echo "${YELLOW}Please place your Cloudflare Origin certificates in the nginx/ssl directory:${NC}"; \
		echo "  - nginx/ssl/origin-certificate.pem"; \
		echo "  - nginx/ssl/private-key.pem"; \
		echo "${YELLOW}You can generate these from the Cloudflare dashboard under SSL/TLS > Origin Server.${NC}"; \
		exit 1; \
	fi

# Clean up all containers and volumes
clean:
	@echo "${YELLOW}This will remove all containers and volumes. Are you sure? [y/N]${NC}"
	@read -r response; \
	if [ "$$response" = "y" ] || [ "$$response" = "Y" ]; then \
		echo "${GREEN}Removing all containers and volumes...${NC}"; \
		$(DOCKER_COMPOSE) down -v; \
		echo "${GREEN}Cleanup completed${NC}"; \
	else \
		echo "${GREEN}Cleanup cancelled${NC}"; \
	fi

# Create an admin user
create-admin:
	@echo "${YELLOW}Creating admin user...${NC}"
	@read -p "Email: " email; \
	read -s -p "Password: " password; \
	echo ""; \
	$(DOCKER_COMPOSE) exec api python -c "from app.auth.users import create_admin_user; import asyncio; asyncio.run(create_admin_user('$$email', '$$password'))"

# Format code with Black
format:
	@echo "${GREEN}Formatting code with Black...${NC}"
	@black app/ main.py

# Lint code with flake8
lint:
	@echo "${GREEN}Linting code with flake8...${NC}"
	@flake8 app/ main.py

# Run tests
test:
	@echo "${GREEN}Running tests...${NC}"
	@pytest