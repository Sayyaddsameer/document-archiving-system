#!/bin/sh
set -e

echo "Starting Vault setup..."

if [ -z "$VAULT_ADDR" ]; then
    export VAULT_ADDR="http://vault:8200"
fi

echo "Waiting for Vault to start..."
while true; do
    STATUS=$(vault status -format=json 2>/dev/null || true)
    if [ -n "$STATUS" ]; then
        break
    fi
    sleep 2
done

INITIALIZED=$(echo "$STATUS" | grep -o '"initialized":true' || echo "false")

if [ "$INITIALIZED" = "false" ]; then
    echo "Initializing Vault..."
    INIT_OUTPUT=$(vault operator init -key-shares=1 -key-threshold=1 -format=json 2>&1)
    UNSEAL_KEY=$(echo "$INIT_OUTPUT" | grep -o '"unseal_keys_b64":\["[^"]*"' | sed 's/.*\["\(.*\)"/\1/')
    ROOT_TOKEN=$(echo "$INIT_OUTPUT" | grep -o '"root_token":"[^"]*"' | sed 's/.*"root_token":"\(.*\)".*/\1/')
    
    echo '{"unseal_key":"'"$UNSEAL_KEY"'","root_token":"'"$ROOT_TOKEN"'"}' > /vault-keys/vault-keys.json
    echo "Vault initialized and keys saved."
else
    echo "Vault is already initialized."
    UNSEAL_KEY=$(grep -o '"unseal_key":"[^"]*"' /vault-keys/vault-keys.json | sed 's/.*"unseal_key":"\(.*\)".*/\1/')
    ROOT_TOKEN=$(grep -o '"root_token":"[^"]*"' /vault-keys/vault-keys.json | sed 's/.*"root_token":"\(.*\)".*/\1/')
fi

echo "Unsealing Vault..."
vault operator unseal "$UNSEAL_KEY" > /dev/null

echo "Logging into Vault..."
vault login "$ROOT_TOKEN" > /dev/null

echo "Enabling KV v2 secrets engine..."
vault secrets enable -path=secret -version=2 kv 2>/dev/null || echo "Secrets engine already enabled, skipping."

echo "Generating and storing secrets..."
if [ -z "$POSTGRES_PASSWORD" ]; then
    POSTGRES_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 32)
fi
if [ -z "$MINIO_ROOT_PASSWORD" ]; then
    MINIO_ROOT_PASSWORD=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | head -c 32)
fi

POSTGRES_USER=${POSTGRES_USER:-archiver}
POSTGRES_DB=${POSTGRES_DB:-documents_db}
MINIO_ROOT_USER=${MINIO_ROOT_USER:-minioadmin_user}

vault kv put secret/app \
    postgres_password="$POSTGRES_PASSWORD" \
    postgres_user="$POSTGRES_USER" \
    postgres_db="$POSTGRES_DB" \
    minio_root_user="$MINIO_ROOT_USER" \
    minio_root_password="$MINIO_ROOT_PASSWORD" > /dev/null

echo "Verifying secrets..."
vault kv get secret/app > /dev/null

echo "Vault setup completed successfully."
exit 0
