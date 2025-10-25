"""Secrets management for AWS, Vault, and Doppler."""

import os
import json
import logging
import hvac
import boto3
from dopplersdk import DopplerSDK

logger = logging.getLogger(__name__)


def load_secrets_from_aws(secret_name):
    """
    Load secrets from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret in AWS Secrets Manager
        
    Returns:
        Dict of secrets or empty dict on error
    """
    try:
        client = boto3.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_name)
        secrets = json.loads(response['SecretString'])
        logger.debug(f"Successfully loaded AWS secret: {secret_name}")
        return secrets
    except Exception as e:
        logger.error(f"Failed to load AWS secret {secret_name}: {e}")
        return {}


def load_secrets_from_vault(secret_path):
    """
    Load secrets from HashiCorp Vault.
    
    Args:
        secret_path: Path to the secret in Vault
        
    Returns:
        Dict of secrets or empty dict on error
    """
    try:
        vault_url = os.getenv('SECRETS_VAULT_URL')
        vault_token = os.getenv('SECRETS_VAULT_TOKEN')
        
        if not vault_url or not vault_token:
            logger.error("Vault URL or token not configured")
            return {}
        
        client = hvac.Client(url=vault_url, token=vault_token)
        if not client.is_authenticated():
            logger.error("Vault authentication failed")
            return {}
        
        response = client.secrets.kv.v2.read_secret_version(path=secret_path)
        secrets = response['data']['data']
        logger.debug(f"Successfully loaded Vault secret: {secret_path}")
        return secrets
    except Exception as e:
        logger.error(f"Failed to load Vault secret {secret_path}: {e}")
        return {}


def load_secrets_from_doppler(secret_name):
    """
    Load secrets from Doppler by secret name.
    
    Args:
        secret_name: Name prefix for secrets in Doppler (e.g., 'twitch', 'youtube')
        
    Returns:
        Dict of secrets or empty dict on error
    """
    try:
        doppler_token = os.getenv('DOPPLER_TOKEN')
        if not doppler_token:
            logger.error("DOPPLER_TOKEN not set")
            return {}
        
        # Get Doppler project and config from environment
        doppler_project = os.getenv('DOPPLER_PROJECT', 'stream-daemon')
        doppler_config = os.getenv('DOPPLER_CONFIG', 'prd')
        
        sdk = DopplerSDK()
        sdk.set_access_token(doppler_token)
        
        # Fetch the specific secret from Doppler
        # Doppler stores secrets as key-value pairs in a project/config
        try:
            # Get all secrets from the specified project and config
            secrets_response = sdk.secrets.list(
                project=doppler_project,
                config=doppler_config
            )
            
            # Filter secrets that match our pattern
            # e.g., if secret_name is "twitch", look for TWITCH_CLIENT_ID, TWITCH_CLIENT_SECRET
            secrets_dict = {}
            if hasattr(secrets_response, 'secrets'):
                all_keys = list(secrets_response.secrets.keys())
                logger.info(f"Doppler connection successful. Found {len(all_keys)} total secrets in project '{doppler_project}', config '{doppler_config}'")
                
                for secret_key, secret_value in secrets_response.secrets.items():
                    # Match secrets with the platform prefix
                    if secret_key.upper().startswith(secret_name.upper()):
                        # Extract the actual key name (e.g., CLIENT_ID from TWITCH_CLIENT_ID)
                        key_suffix = secret_key[len(secret_name)+1:].lower()  # +1 for underscore
                        secrets_dict[key_suffix] = secret_value.get('computed', secret_value.get('raw', ''))
                
                if not secrets_dict:
                    logger.debug(f"No secrets found with prefix '{secret_name.upper()}_*'. Available secrets: {[k for k in all_keys if not k.startswith('DOPPLER_')]}")
            
            return secrets_dict
        except Exception as e:
            logger.error(f"Failed to fetch Doppler secret {secret_name}: {e}")
            return {}
            
    except Exception as e:
        logger.error(f"Failed to configure Doppler: {e}")
        return {}


def get_secret(platform, key, secret_name_env=None, secret_path_env=None, doppler_secret_env=None):
    """
    Get a secret value with priority:
    1. Secrets manager (AWS/Vault/Doppler) - HIGHEST PRIORITY if credentials exist
    2. Environment variable (.env file) - FALLBACK
    3. None if not found
    
    This ensures production secrets in secrets managers override .env defaults.
    
    Args:
        platform: Platform name (e.g., 'Twitch', 'YouTube')
        key: Secret key (e.g., 'client_id', 'api_key')
        secret_name_env: AWS Secrets Manager env var name
        secret_path_env: HashiCorp Vault env var name
        doppler_secret_env: Doppler secret name env var
        
    Returns:
        Secret value or None if not found
    """
    try:
        # Priority 1: Try Doppler first if DOPPLER_TOKEN exists (auto-detect)
        if os.getenv('DOPPLER_TOKEN') and doppler_secret_env:
            secret_name = os.getenv(doppler_secret_env)
            if secret_name:
                secrets = load_secrets_from_doppler(secret_name)
                secret_value = secrets.get(key)
                if secret_value:
                    return secret_value
                
                # Special case: For keys like GEMINI_API_KEY that aren't prefixed in Doppler,
                # try getting the direct key (GEMINI_API_KEY) from all Doppler secrets
                try:
                    doppler_token = os.getenv('DOPPLER_TOKEN')
                    if doppler_token:
                        doppler_project = os.getenv('DOPPLER_PROJECT', 'stream-daemon')
                        doppler_config = os.getenv('DOPPLER_CONFIG', 'prd')
                        
                        sdk = DopplerSDK()
                        sdk.set_access_token(doppler_token)
                        secrets_response = sdk.secrets.list(project=doppler_project, config=doppler_config)
                        
                        if hasattr(secrets_response, 'secrets'):
                            # Try direct key lookup (e.g., GEMINI_API_KEY)
                            direct_key = key.upper()
                            if direct_key in secrets_response.secrets:
                                return secrets_response.secrets[direct_key].get('computed', 
                                       secrets_response.secrets[direct_key].get('raw', ''))
                except Exception as e:
                    logger.debug(f"Direct key lookup failed for {key}: {e}")
        
        # Check which secrets manager is enabled (for AWS/Vault)
        secret_manager = os.getenv('SECRETS_SECRET_MANAGER', 'none').lower()
        
        # Try AWS Secrets Manager
        if secret_manager == 'aws' and secret_name_env:
            secret_name = os.getenv(secret_name_env)
            if secret_name:
                secrets = load_secrets_from_aws(secret_name)
                secret_value = secrets.get(key)
                if secret_value:
                    return secret_value
        
        # Try HashiCorp Vault
        elif secret_manager == 'vault' and secret_path_env:
            secret_path = os.getenv(secret_path_env)
            if secret_path:
                secrets = load_secrets_from_vault(secret_path)
                secret_value = secrets.get(key)
                if secret_value:
                    return secret_value
        
        # Priority 2: Fallback to environment variable (.env file)
        env_key = f"{platform.upper()}_{key.upper()}"
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting secret for {platform}.{key}: {e}")
        return None
