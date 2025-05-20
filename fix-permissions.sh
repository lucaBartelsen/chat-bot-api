# File: fix-permissions.sh
# Path: fanfix-api/fix-permissions.sh

#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Fixing permissions for the FanFix API...${NC}"

# Fix Prisma permissions in the container
echo -e "${YELLOW}Fixing Prisma permissions in the container...${NC}"
docker-compose exec api sh -c "mkdir -p /app/.cache/prisma-python && chmod -R 777 /app/.cache"
docker-compose exec api sh -c "chmod -R 777 /usr/local/lib/python3.10/site-packages/prisma"

# Reset the OpenAPI schema
echo -e "${YELLOW}Resetting OpenAPI schema...${NC}"
docker-compose exec api curl -s http://localhost:8000/reload-openapi
sleep 2

# Run the diagnostics
echo -e "${YELLOW}Running diagnostic checks...${NC}"
docker-compose exec api curl -s http://localhost:8000/diagnostics/info

echo -e "${GREEN}Permissions fixed!${NC}"
echo -e "Try accessing the API documentation at https://chatsassistant.com/docs"
echo -e "If it's still not working, check the diagnostics at https://chatsassistant.com/diagnostics/info"
echo -e "A static fallback is available at https://chatsassistant.com/static/api-docs.html"