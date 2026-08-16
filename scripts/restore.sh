#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ==========================================
# CONFIGURATION
# ==========================================

DB_NAME="StrachyBot"
DB_USER="postgres"

# Dynamically locate directories relative to this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_REPO_DIR="$(cd "${SCRIPT_DIR}/../backups" && pwd)"
COMPOSE_FILE="$(cd "${SCRIPT_DIR}/.." && pwd)/docker-compose.yml"

# ==========================================
# RESOLVE BACKUP FILE
# ==========================================

# If a specific backup file was passed as an argument, use it; otherwise use the backup.sql file
if [ -n "$1" ]; then
    RESTORE_FILE="$1"
else
    RESTORE_FILE=${BACKUP_REPO_DIR}"/backup.sql"
fi

if [ -z "$RESTORE_FILE" ] || [ ! -f "$RESTORE_FILE" ]; then
    echo "Error: No backup file found in '$BACKUP_REPO_DIR' or specified path is invalid." >&2
    exit 1
fi

if [ ! -f "$COMPOSE_FILE" ]; then
    echo "Error: Compose file '$COMPOSE_FILE' does not exist." >&2
    exit 1
fi

# Locate container ID for the 'postgres' service belonging ONLY to this compose stack
CONTAINER_ID=$(docker compose -f "$COMPOSE_FILE" ps -q postgres)

if [ -z "$CONTAINER_ID" ]; then
    echo "Error: Postgres container for project at '$COMPOSE_FILE' is not running." >&2
    exit 1
fi

# ==========================================
# CONFIRMATION & RESTORE
# ==========================================

echo "=================================================="
echo "          DATABASE RESTORE WARNING                "
echo "=================================================="
echo "Target Container ID : ${CONTAINER_ID}"
echo "Target Database     : ${DB_NAME}"
echo "Backup File         : ${RESTORE_FILE}"
echo "=================================================="
read -p "WARNING: This will overwrite data in '${DB_NAME}'. Continue? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore aborted by user."
    exit 0
fi

echo "Dropping and recreating public schema to ensure a clean state..."
docker exec -i "$CONTAINER_ID" psql -U "$DB_USER" -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" > /dev/null

echo "Restoring database state from SQL file..."
cat "$RESTORE_FILE" | docker exec -i "$CONTAINER_ID" psql -U "$DB_USER" -d "$DB_NAME" > /dev/null

echo "Database restore complete!"
