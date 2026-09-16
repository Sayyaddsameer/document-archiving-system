#!/bin/sh
set -e

echo "Starting MinIO entrypoint..."

export VAULT_ADDR=${VAULT_ADDR:-"http://vault:8200"}

echo "Waiting for vault-keys.json to be available..."
while [ ! -f /vault-keys/vault-keys.json ]; do
    sleep 2
done

ROOT_TOKEN=$(grep -o '"root_token":"[^"]*"' /vault-keys/vault-keys.json | sed 's/.*"root_token":"\(.*\)".*/\1/')

echo "Fetching secrets from Vault..."
while true; do
    SECRETS=$(curl -s -H "X-Vault-Token: $ROOT_TOKEN" $VAULT_ADDR/v1/secret/data/app || true)
    if echo "$SECRETS" | grep -q '"minio_root_user"'; then
        break
    fi
    sleep 2
done

export MINIO_ROOT_USER=$(echo "$SECRETS" | sed 's/.*"minio_root_user":"\([^"]*\)".*/\1/')
export MINIO_ROOT_PASSWORD=$(echo "$SECRETS" | sed 's/.*"minio_root_password":"\([^"]*\)".*/\1/')

echo "Starting MinIO server..."
exec minio server /data --console-address ":9001"
