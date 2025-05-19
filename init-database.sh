# File: init-database.sh
# Path: fanfix-api/init-database.sh

#!/bin/bash

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Initializing database...${NC}"

# Wait for database to be ready
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
until PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U postgres -d chat_assistant_db -c '\q'; do
  echo "Database not ready yet, retrying in 5 seconds..."
  sleep 5
done

echo -e "${GREEN}Database is ready!${NC}"

# Enable pgvector extension
echo -e "${YELLOW}Enabling pgvector extension...${NC}"
PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U postgres -d chat_assistant_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo -e "${GREEN}Database initialization completed!${NC}"

# Run the application
exec uvicorn main:app --host 0.0.0.0 --port 8000