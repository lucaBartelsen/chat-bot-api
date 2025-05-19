# File: setup.sh
# Path: fanfix-api/setup.sh

#!/bin/bash

# Setup script for the FanFix ChatAssist API with Docker and Cloudflare

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting setup for ChatAssist API...${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p nginx/conf.d nginx/ssl nginx/www

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
    cp .env.example .env
    echo -e "${RED}Please update the .env file with your actual values.${NC}"
fi

# Check for Cloudflare SSL certificates
if [ ! -f nginx/ssl/origin-certificate.pem ] || [ ! -f nginx/ssl/private-key.pem ]; then
    echo -e "${RED}Cloudflare Origin certificates not found.${NC}"
    echo -e "${YELLOW}Please place your Cloudflare Origin certificates in the nginx/ssl directory:${NC}"
    echo -e "  - nginx/ssl/origin-certificate.pem"
    echo -e "  - nginx/ssl/private-key.pem"
    echo -e "${YELLOW}You can generate these from the Cloudflare dashboard under SSL/TLS > Origin Server.${NC}"
fi

# Setup directory permissions
echo -e "${YELLOW}Setting up directory permissions...${NC}"
chmod +x setup.sh

# Creating default placeholder files if they don't exist
if [ ! -f nginx/www/index.html ]; then
    echo -e "${YELLOW}Creating placeholder index.html...${NC}"
    cp nginx-www-index.html nginx/www/index.html
fi

echo -e "${GREEN}Setup completed!${NC}"
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Make sure your .env file is properly configured"
echo -e "2. Place your Cloudflare Origin certificates in the nginx/ssl directory"
echo -e "3. Run: docker-compose up -d"
echo -e "4. Configure DNS in Cloudflare to point to your server's IP address"
echo -e "5. Visit https://chatsassistant.com to verify your setup"