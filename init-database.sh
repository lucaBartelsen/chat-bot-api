#!/bin/bash

set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Initializing database...${NC}"

# Make sure Prisma cache permissions are correct
echo -e "${YELLOW}Ensuring Prisma cache permissions...${NC}"
mkdir -p /app/.cache/prisma-python
chmod -R 777 /app/.cache/prisma-python

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

# Generate Prisma client (again to ensure it's up to date)
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
exec uvicorn main:app --host 0.0.0.0 --port 8000