#!/bin/bash

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Initializing database...${NC}"

# First check if we can connect to PostgreSQL at all
echo -e "${YELLOW}Checking PostgreSQL connection...${NC}"
max_attempts=30
attempt=0
while true; do
  attempt=$((attempt+1))
  echo "Attempt $attempt/$max_attempts: Testing connection with command: PGPASSWORD=*** psql -h db -U postgres -c '\q'"
  
  # Run the command and capture both stdout and stderr
  connection_output=$(PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U postgres -c '\q' 2>&1)
  connection_status=$?
  
  # Display the complete output
  if [ -n "$connection_output" ]; then
    echo "Command output: $connection_output"
  fi
  
  # Check if the command was successful
  if [ $connection_status -eq 0 ]; then
    echo -e "${GREEN}Successfully connected to PostgreSQL!${NC}"
    break
  fi
  
  # Check if we've reached the maximum number of attempts
  if [ $attempt -eq $max_attempts ]; then
    echo -e "${RED}Failed to connect to PostgreSQL after $max_attempts attempts. Exiting.${NC}"
    echo -e "${RED}Last error: $connection_output${NC}"
    exit 1
  fi
  
  echo "PostgreSQL not ready yet, retry $attempt/$max_attempts (waiting 5 seconds)..."
  sleep 5
done

# Ensure the database exists
echo -e "${YELLOW}Ensuring database exists...${NC}"
PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U postgres -c "CREATE DATABASE chat_assistant_db WITH ENCODING 'UTF8' OWNER postgres;" 2>/dev/null || true
echo -e "${GREEN}Database connection established and database exists.${NC}"

# Enable pgvector extension
echo -e "${YELLOW}Enabling pgvector extension...${NC}"
PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U postgres -d chat_assistant_db -c "CREATE EXTENSION IF NOT EXISTS vector;"

# Generate Prisma client (just to be sure it's up to date)
echo -e "${YELLOW}Generating Prisma client...${NC}"
prisma generate

# Create vector index if needed (after Prisma has created the tables)
echo -e "${YELLOW}Setting up vector indexes (will be retried by the application if tables don't exist yet)...${NC}"
PGPASSWORD=$POSTGRES_PASSWORD psql -h db -U postgres -d chat_assistant_db -c "
DO \$\$
BEGIN
  IF EXISTS (
    SELECT 1
    FROM information_schema.tables
    WHERE table_name = 'VectorStore'
  ) THEN
    IF NOT EXISTS (
      SELECT 1
      FROM pg_indexes
      WHERE indexname = 'vectorstore_embedding_idx'
    ) THEN
      EXECUTE 'CREATE INDEX vectorstore_embedding_idx ON \"VectorStore\" USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)';
      RAISE NOTICE 'Vector index created';
    ELSE
      RAISE NOTICE 'Vector index already exists';
    END IF;
  ELSE
    RAISE NOTICE 'VectorStore table does not exist yet';
  END IF;
END
\$\$;
"

echo -e "${GREEN}Database initialization completed!${NC}"

# Run the application
echo -e "${GREEN}Starting application...${NC}"
exec uvicorn main:app --host 0.0.0.0 --port 8000