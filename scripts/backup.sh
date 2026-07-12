#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# ==========================================
# CONFIGURATION
# ==========================================

CURRENT_DATE=$(date +"%Y-%m-%d_%H-%M-%S")
CONTAINER_NAME="StrachyBotDB"
DB_NAME="StrachyBot"
DB_USER="postgres"

# Absolute paths are required for cron jobs!
# Dynamically locate the 'backups' directory from the 'scripts' directory (BASH_SOURCE[0])
BACKUP_REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../backups" && pwd)"

BACKUP_FILE_NAME="backup.sql"
FULL_BACKUP_PATH="${BACKUP_REPO_DIR}/${BACKUP_FILE_NAME}"

# Git configuration overrides for the backup robot
GIT_USER="backup-bot"
GIT_EMAIL="backup-bot@strachy.bot"

# ==========================================
# BACKUP SEQUENCE
# ==========================================

echo "Starting database backup sequence [${CURRENT_DATE}]..."

if [ ! -d "$BACKUP_REPO_DIR" ]; then
    echo "Error: Backup directory '$BACKUP_REPO_DIR' does not exist." >&2
    exit 1
fi

if [ ! "$(docker ps -q -f name=^${CONTAINER_NAME}$)" ]; then
    echo "Error: Docker container '${CONTAINER_NAME}' is not running." >&2
    exit 1
fi

BACKUP_EXISTS=

if [[ -f "${FULL_BACKUP_PATH}" ]]; then
    BACKUP_EXISTS=true
fi

echo "Extracting database contents from the '${CONTAINER_NAME}' Docker container..."
docker exec -t "$CONTAINER_NAME" pg_dump -U "$DB_USER" -d "$DB_NAME" > "$FULL_BACKUP_PATH"
echo "SQL dump successfully written to: ${FULL_BACKUP_PATH}."

echo "Tracking changes to '${BACKUP_FILE_NAME}'..."
cd "$BACKUP_REPO_DIR"
git add "$BACKUP_FILE_NAME"

if [[ ! -z "${BACKUP_EXISTS}" ]]; then
    echo "Filtering database changes..."
    # Filter out git headers (+++ or ---) and '\restrict' and '\unrestrict' lines
    BACKUP_CHANGED=$(git diff --cached | grep -E '^[+-][^+-]' | grep -vE '(restrict|unrestrict)' || true)

    # Revert backup if no changes occurred and exit
    if [[ -z "${BACKUP_CHANGED}" ]]; then
        echo "No meaningful database changes detected. Skipping commit."
        git restore --staged "$BACKUP_FILE_NAME"
        git restore "$BACKUP_FILE_NAME"
        exit 0
    fi
fi

echo "Committing the changes..."
git -c user.name="$GIT_USER" -c user.email="$GIT_EMAIL" commit -m "[${CURRENT_DATE}] automatic backup."

echo "Pushing changes to the remote repository..."
git push origin main 

echo "Database backup complete!"