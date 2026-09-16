import json
import os
import logging

import hvac

logger = logging.getLogger(__name__)

VAULT_ADDR = os.environ.get("VAULT_ADDR", "http://vault:8200")
VAULT_TOKEN_PATH = os.environ.get("VAULT_TOKEN_PATH", "/vault-keys/vault-keys.json")


def load_vault_token():
    """Read the root token from the vault-keys.json file."""
    with open(VAULT_TOKEN_PATH, "r") as f:
        keys = json.load(f)
    return keys["root_token"]


def fetch_secrets():
    """Connect to Vault and fetch application secrets from secret/data/app."""
    token = load_vault_token()
    client = hvac.Client(url=VAULT_ADDR, token=token)
    
    if not client.is_authenticated():
        raise RuntimeError("Failed to authenticate with Vault")
    
    logger.info("Authenticated with Vault at %s", VAULT_ADDR)
    
    response = client.secrets.kv.v2.read_secret_version(
        path="app",
        mount_point="secret",
    )
    
    secrets = response["data"]["data"]
    logger.info("Successfully fetched secrets from Vault")
    return secrets
