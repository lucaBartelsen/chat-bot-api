#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print steps
print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

# Function to print warnings
print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Function to print errors
print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

# Check if Python is installed
print_step "Checking Python installation..."
if ! command -v python3 &> /dev/null
then
    print_error "Python 3 is not installed. Please install it and try again."
    exit 1
fi

# Create virtual environment
print_step "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
print_step "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
print_step "Installing dependencies..."
pip install -r requirements.txt

# Ensure SSL directory exists
print_step "Setting up SSL directory structure..."
mkdir -p nginx/ssl
mkdir -p nginx/conf.d
mkdir -p nginx/www

# Check if SSL certificates exist
if [ ! -f nginx/ssl/origin-certificate.pem ] || [ ! -f nginx/ssl/private-key.pem ]; then
    print_warning "SSL certificates not found in nginx/ssl directory."
    print_warning "Please place your 'origin-certificate.pem' and 'private-key.pem' files in the nginx/ssl directory."
else
    print_step "Setting proper permissions for SSL certificates..."
    chmod 644 nginx/ssl/origin-certificate.pem
    chmod 600 nginx/ssl/private-key.pem
fi

# Check if PostgreSQL is running
print_step "Checking PostgreSQL connection..."
if command -v pg_isready &> /dev/null; then
    pg_isready -h localhost -p 5432
    if [ $? -ne 0 ]; then
        print_warning "PostgreSQL is not running. Please start PostgreSQL."
    else
        print_step "PostgreSQL is running."
    fi
else
    print_warning "pg_isready not found. Make sure PostgreSQL is running."
fi

# Initialize database
print_step "Initializing database (you need to have PostgreSQL running)..."
python -c "from app.core.database import init_db; init_db()"

print_step "Setup complete!"
print_step "Don't forget to:"
print_step "1. Create default.conf in nginx/conf.d directory"
print_step "2. Create index.html in nginx/www directory if needed"
print_step "3. Rename .env.docker to .env for Docker Compose"
print_step "Run 'uvicorn main:app --reload' to start the development server."
print_step "Or use 'docker-compose up' to start the containerized application."