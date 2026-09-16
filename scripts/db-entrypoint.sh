#!/bin/sh
set -e

echo "Starting database entrypoint..."

export VAULT_ADDR=${VAULT_ADDR:-"http://vault:8200"}

echo "Waiting for vault-keys.json to be available..."
while [ ! -f /vault-keys/vault-keys.json ]; do
    sleep 2
done

ROOT_TOKEN=$(grep -o '"root_token":"[^"]*"' /vault-keys/vault-keys.json | sed 's/.*"root_token":"\(.*\)".*/\1/')

echo "Installing dependencies..."
apk add --no-cache curl jq > /dev/null 2>&1

echo "Fetching secrets from Vault..."
while true; do
    SECRETS=$(curl -s -H "X-Vault-Token: $ROOT_TOKEN" $VAULT_ADDR/v1/secret/data/app || true)
    if echo "$SECRETS" | grep -q '"postgres_password"'; then
        break
    fi
    sleep 2
done

export POSTGRES_PASSWORD=$(echo "$SECRETS" | jq -r '.data.data.postgres_password')
export POSTGRES_USER=$(echo "$SECRETS" | jq -r '.data.data.postgres_user')
export POSTGRES_DB=$(echo "$SECRETS" | jq -r '.data.data.postgres_db')

echo "Starting PostgreSQL..."
exec docker-entrypoint.sh postgres
