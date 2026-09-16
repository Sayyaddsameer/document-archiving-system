#!/bin/sh
set -e

echo "Starting MinIO initialization..."

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

MINIO_ROOT_USER=$(echo "$SECRETS" | sed 's/.*"minio_root_user":"\([^"]*\)".*/\1/')
MINIO_ROOT_PASSWORD=$(echo "$SECRETS" | sed 's/.*"minio_root_password":"\([^"]*\)".*/\1/')

echo "Waiting for MinIO to be reachable..."
while ! curl -s http://minio:9000/minio/health/live > /dev/null; do
    sleep 2
done

echo "Configuring MinIO client alias..."
mc alias set myminio http://minio:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" > /dev/null

echo "Creating documents bucket..."
mc mb myminio/documents --ignore-existing > /dev/null

echo "Setting bucket policy to private..."
mc anonymous set none myminio/documents > /dev/null

echo "MinIO initialization completed successfully."
exit 0
