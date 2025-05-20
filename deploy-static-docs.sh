# File: deploy-static-docs.sh
# Path: fanfix-api/deploy-static-docs.sh

#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deploying static API documentation...${NC}"

# Create directory if it doesn't exist
mkdir -p nginx/www/static

# Copy documentation files
echo -e "${YELLOW}Copying documentation files...${NC}"
cp -f static-docs.html nginx/www/static/api-docs.html
cp -f static-docs.html nginx/www/static/index.html

# Create a backup of swagger UI
echo -e "${YELLOW}Creating Swagger UI backup...${NC}"
mkdir -p nginx/www/static/swagger
cp -f nginx/www/static/api-docs.html nginx/www/static/swagger/index.html

# Make sure permissions are correct
echo -e "${YELLOW}Setting permissions...${NC}"
chmod -R 755 nginx/www/static

echo -e "${GREEN}Static documentation deployed successfully!${NC}"
echo -e "Static docs available at:"
echo -e "  - /static/api-docs.html"
echo -e "  - /static/swagger/"

# Check if we need to restart nginx
read -p "Do you want to restart nginx to apply changes? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo -e "${YELLOW}Restarting nginx...${NC}"
    docker-compose restart nginx
    echo -e "${GREEN}Nginx restarted.${NC}"
fi