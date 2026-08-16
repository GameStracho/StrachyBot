#!/usr/bin/env bash

set -e

ENV_FILE=".env"
EXAMPLE_ENV_FILE=".env.example"

echo "=========================================="
echo "           🤖 StrachyBot Setup            "
echo "=========================================="

# 1. Ensure .env exists
if [ ! -f "$ENV_FILE" ]; then
    if [ -f "$EXAMPLE_ENV_FILE" ]; then
        echo "📄 $ENV_FILE file not found. Copying from $EXAMPLE_ENV_FILE..."
        cp "$EXAMPLE_ENV_FILE" "$ENV_FILE"
    else
        echo "❌ Error: Neither $ENV_FILE nor $EXAMPLE_ENV_FILE was found!"
        exit 1
    fi
fi

# Function to read a key's current value from .env
get_env_val() {
    local key="$1"
    grep "^${key}=" "$ENV_FILE" 2>/dev/null | cut -d '=' -f2- | tr -d '\r'
}

# Function to safely update or append a key in .env
update_env_val() {
    local key="$1"
    local value="$2"

    if grep -q "^${key}=" "$ENV_FILE"; then
        # Handle sed escape characters safely
        awk -v k="$key" -v v="$value" '
            BEGIN { FS="=" }
            $1 == k { print k "=" v; next }
            { print }
        ' "$ENV_FILE" > "${ENV_FILE}.tmp" && mv "${ENV_FILE}.tmp" "$ENV_FILE"
    else
        echo "${key}=${value}" >> "$ENV_FILE"
    fi
}

# 2. Check & Prompt for Discord Token
EXISTING_TOKEN=$(get_env_val "DISCORD_TOKEN")

if [ -z "$EXISTING_TOKEN" ] || [ "$EXISTING_TOKEN" = "your-token-here" ]; then
    echo ""
    echo "🔑 Discord Token is required."
    read -rp "Please enter your DISCORD_TOKEN: " USER_TOKEN
    
    while [ -z "$USER_TOKEN" ]; do
        echo "⚠️ Token cannot be empty!"
        read -rp "Please enter your DISCORD_TOKEN: " USER_TOKEN
    done
    
    update_env_val "DISCORD_TOKEN" "$USER_TOKEN"
    echo "✅ Discord Token saved."
else
    echo "✅ Existing Discord Token detected. (Skipping token prompt)"
fi

# 3. Check & Generate Database Password
EXISTING_DB_PASS=$(get_env_val "DATABASE_PASSWORD")

if [ -z "$EXISTING_DB_PASS" ] || [ "$EXISTING_DB_PASS" = "your-secret-password-here" ]; then
    # Generate a random 32-character base64 password
    NEW_DB_PASS=$(openssl rand -base64 32 | tr -d '=+/')
    update_env_val "DATABASE_PASSWORD" "$NEW_DB_PASS"
    echo "🔑 Generated secure database password."
fi

# 4. Sync local CONNECTION_STRING with the active password and port
CURRENT_PG_PORT=$(get_env_val "POSTGRES_PORT")
PG_PORT="${CURRENT_PG_PORT:-5432}"
NEW_CONN_STR="postgresql+asyncpg://postgres:${EXISTING_DB_PASS}@localhost:${PG_PORT}/StrachyBot"
update_env_val "CONNECTION_STRING" "$NEW_CONN_STR"
echo "✅ CONNECTION_STRING updated with active database credentials."

# 5. Optional Port Configurations
echo ""
read -rp "Do you want to configure custom ports for Adminer / Postgres? [y/N]: " CONFIGURE_PORTS

if [[ "$CONFIGURE_PORTS" =~ ^[Yy]$ ]]; then
    CURR_ADMINER_PORT=$(get_env_val "ADMINER_PORT")
    read -rp "Enter ADMINER_PORT [Current: ${CURR_ADMINER_PORT:-8080}]: " INPUT_ADMINER_PORT
    NEW_ADMINER_PORT="${INPUT_ADMINER_PORT:-${CURR_ADMINER_PORT:-8080}}"
    update_env_val "ADMINER_PORT" "$NEW_ADMINER_PORT"

    CURR_POSTGRES_PORT=$(get_env_val "POSTGRES_PORT")
    read -rp "Enter POSTGRES_PORT [Current: ${CURR_POSTGRES_PORT:-5432}]: " INPUT_POSTGRES_PORT
    NEW_POSTGRES_PORT="${INPUT_POSTGRES_PORT:-${CURR_POSTGRES_PORT:-5432}}"
    update_env_val "POSTGRES_PORT" "$NEW_POSTGRES_PORT"

    # Re-sync connection string with custom postgres port
    NEW_CONN_STR="postgresql+asyncpg://postgres:${EXISTING_DB_PASS}@localhost:${NEW_POSTGRES_PORT}/StrachyBot"
    update_env_val "CONNECTION_STRING" "$NEW_CONN_STR"
    echo "✅ Custom ports saved and connection string updated."
fi

# 6. Mode Selection (Development vs Production)
CURRENT_PROFILE=$(get_env_val "COMPOSE_PROFILES")

echo ""
echo "Select environment mode:"
echo "  1) Development (Runs DB + Adminer in Docker, Bot locally via Python)"
echo "  2) Production  (Runs Bot + DB + Adminer inside Docker)"
if [ -n "$CURRENT_PROFILE" ]; then
    echo "  (Current profile set to: $CURRENT_PROFILE)"
fi

read -rp "Enter choice [1 or 2]: " MODE_CHOICE

case "$MODE_CHOICE" in
    1)
        SELECTED_PROFILE="development"
        ;;
    2)
        SELECTED_PROFILE="production"
        ;;
    *)
        echo "⚠️ Invalid choice. Keeping current profile."
        SELECTED_PROFILE=$CURRENT_PROFILE
        ;;
esac

update_env_val "COMPOSE_PROFILES" "$SELECTED_PROFILE"
echo "✅ Environment configured for: $SELECTED_PROFILE"

# 7. Optional Virtual Environment Setup for Development
if [ "$SELECTED_PROFILE" = "development" ]; then
    echo ""
    echo "🐍 Setting up Python Virtual Environment..."
    
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        echo "✅ Created .venv directory."
    fi

    # Activate virtualenv inside the subshell to install dependencies
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate

        pip install --upgrade pip -q
        pip install -r requirements.txt -q

        if [ -f "requirements-dev.txt" ]; then
            pip install -r requirements-dev.txt -q
        fi

        echo "✅ Installed dependencies into .venv."
    fi
fi

echo ""
echo "=========================================="
echo "🎉 Setup complete! Next steps:"
echo "=========================================="

if [ "$SELECTED_PROFILE" = "development" ]; then
    echo "1. Start database:  docker compose up -d"
    echo "2. Run migrations:  alembic upgrade head"
    echo "3. Activate venv:   source .venv/bin/activate"
    echo "4. Launch bot:      python src/main.py"
else
    echo "1. Build and run all services in Docker:"
    echo "   docker compose up --build -d"
fi
echo "=========================================="
