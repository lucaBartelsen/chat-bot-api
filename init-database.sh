#!/bin/bash

# DO NOT USE set -e here as we want to continue even if commands fail

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting debug script...${NC}"

# Debug: Check if the script can reach the db hostname
echo -e "${YELLOW}Debug: Testing hostname resolution...${NC}"
getent hosts db || echo "Failed to resolve db hostname"

# Debug: Print environment variables
echo -e "${YELLOW}Debug: Environment variables...${NC}"
echo "POSTGRES_PASSWORD exists: $(if [ -n "$POSTGRES_PASSWORD" ]; then echo "YES"; else echo "NO"; fi)"
echo "DATABASE_URL exists: $(if [ -n "$DATABASE_URL" ]; then echo "YES"; else echo "NO"; fi)"
echo "DATABASE_URL: ${DATABASE_URL//@*/@masked}"

# Check if psql is installed
if command -v psql >/dev/null 2>&1; then
    echo -e "${GREEN}psql is installed${NC}"
else
    echo -e "${RED}psql is not installed!${NC}"
    # Instead of exiting, try using another method to test connectivity
    echo "Will try using alternatives..."
fi

# Try to connect with explicit values rather than environment variables
echo -e "${YELLOW}Attempt to connect with hard-coded values...${NC}"
psql -h db -U postgres -c '\q'
echo "Exit status of direct psql command: $?"

# If the above didn't work, try with PGPASSWORD
echo -e "${YELLOW}Attempt to connect with PGPASSWORD...${NC}"
PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U postgres -c '\q'
echo "Exit status of PGPASSWORD psql command: $?"

# Try a simpler loop
echo -e "${YELLOW}Starting a basic connection loop...${NC}"
for i in {1..5}; do
    echo "Attempt $i: Connecting to PostgreSQL..."
    PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U postgres -c '\q'
    status=$?
    echo "Status: $status"
    
    if [ $status -eq 0 ]; then
        echo -e "${GREEN}Successfully connected!${NC}"
        break
    else
        echo -e "${RED}Failed to connect, retrying...${NC}"
        sleep 5
    fi
done

echo "Debug script completed"