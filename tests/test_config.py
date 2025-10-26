"""
Configuration and Secrets Loading Tests

Tests that configuration is loaded correctly from environment variables
and secrets managers (Doppler, AWS Secrets Manager, HashiCorp Vault).
"""

import pytest
import os
from stream_daemon.config import get_config, get_secret, get_bool_config, get_int_config


class TestConfigLoading:
    """Test configuration loading from environment variables."""
    
    def test_get_config_returns_value(self):
        """Test that get_config returns environment variable values."""
        # Set a test value (format: SECTION_KEY)
        os.environ['TEST_CONFIG'] = 'test_value'
        result = get_config('Test', 'config')
        assert result == 'test_value'
        
        # Cleanup
        del os.environ['TEST_CONFIG']
    
    def test_get_config_default_value(self):
        """Test that get_config returns default when var not set."""
        result = get_config('Nonexistent', 'var', default='default_value')
        assert result == 'default_value'
    
    def test_get_bool_config_true_values(self):
        """Test that get_bool_config correctly parses true values."""
        true_values = ['true', 'True', 'TRUE', '1', 'yes', 'Yes', 'YES']
        
        for val in true_values:
            os.environ['TEST_BOOL'] = val
            result = get_bool_config('Test', 'bool', False)
            assert result is True, f"Failed for value: {val}"
        
        # Cleanup
        del os.environ['TEST_BOOL']
    
    def test_get_bool_config_false_values(self):
        """Test that get_bool_config correctly parses false values."""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO']
        
        for val in false_values:
            os.environ['TEST_BOOL'] = val
            result = get_bool_config('Test', 'bool', True)
            assert result is False, f"Failed for value: {val}"
        
        # Cleanup
        del os.environ['TEST_BOOL']
    
    def test_get_int_config(self):
        """Test that get_int_config parses integers correctly."""
        os.environ['TEST_INT'] = '42'
        result = get_int_config('Test', 'int', 0)
        assert result == 42
        assert isinstance(result, int)
        
        # Cleanup
        del os.environ['TEST_INT']
    
    def test_get_int_config_invalid_fallback(self):
        """Test that get_int_config uses default for invalid values."""
        os.environ['TEST_INT'] = 'not_a_number'
        result = get_int_config('Test', 'int', 100)
        assert result == 100
        
        # Cleanup
        del os.environ['TEST_INT']


class TestSecretLoading:
    """Test secret loading from secrets managers."""
    
    def test_doppler_secret_loading(self, skip_if_no_secrets):
        """Test loading secrets from Doppler."""
        secret_manager = os.getenv('SECRETS_SECRET_MANAGER', '').lower()
        if secret_manager != 'doppler':
            pytest.skip("Doppler not configured (SECRETS_SECRET_MANAGER != doppler)")
        
        # Test loading a Twitch secret
        client_id = get_secret(
            'Twitch', 
            'client_id',
            doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME'
        )
        
        assert client_id is not None, "Failed to load Twitch client_id from Doppler"
        assert len(client_id) > 0, "Twitch client_id is empty"
        # Secret should not be 'NOT_SET' or similar placeholder
        assert client_id.lower() not in ['not_set', 'none', 'null', ''], "Twitch client_id appears to be placeholder"
    
    def test_aws_secret_loading(self, skip_if_no_secrets):
        """Test loading secrets from AWS Secrets Manager."""
        secret_manager = os.getenv('SECRETS_SECRET_MANAGER', '').lower()
        if secret_manager != 'aws':
            pytest.skip("AWS Secrets Manager not configured (SECRETS_SECRET_MANAGER != aws)")
        
        # Test loading a Twitch secret
        client_id = get_secret(
            'Twitch',
            'client_id',
            secret_name_env='SECRETS_AWS_TWITCH_SECRET_NAME'
        )
        
        assert client_id is not None, "Failed to load Twitch client_id from AWS"
        assert len(client_id) > 0, "Twitch client_id is empty"
    
    def test_vault_secret_loading(self, skip_if_no_secrets):
        """Test loading secrets from HashiCorp Vault."""
        secret_manager = os.getenv('SECRETS_SECRET_MANAGER', '').lower()
        if secret_manager != 'vault':
            pytest.skip("Vault not configured (SECRETS_SECRET_MANAGER != vault)")
        
        # Test loading a Twitch secret
        client_id = get_secret(
            'Twitch',
            'client_id',
            secret_path_env='SECRETS_VAULT_TWITCH_SECRET_PATH'
        )
        
        assert client_id is not None, "Failed to load Twitch client_id from Vault"
        assert len(client_id) > 0, "Twitch client_id is empty"
    
    def test_secret_priority_manager_over_env(self):
        """Test that secrets manager takes priority over environment variables."""
        # Check if ANY secrets manager is actually configured with credentials
        has_doppler = bool(os.getenv('DOPPLER_TOKEN'))
        has_aws = bool(os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'))
        has_vault = bool(os.getenv('SECRETS_VAULT_URL') and os.getenv('SECRETS_VAULT_TOKEN'))
        
        if not (has_doppler or has_aws or has_vault):
            pytest.skip("No secrets manager credentials available (expected in CI)")
        
        # Set an environment variable
        os.environ['TWITCH_CLIENT_ID'] = 'env_var_value'
        
        # Get secret (should come from secrets manager, not env var)
        client_id = get_secret(
            'Twitch',
            'client_id',
            doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME',
            secret_name_env='SECRETS_AWS_TWITCH_SECRET_NAME',
            secret_path_env='SECRETS_VAULT_TWITCH_SECRET_PATH'
        )
        
        # Cleanup
        del os.environ['TWITCH_CLIENT_ID']
        
        # If secret manager is configured, it should override env var
        if client_id:
            assert client_id != 'env_var_value', "Secrets manager should override environment variable"


class TestSecretMasking:
    """Test that secrets are properly masked in logs and output."""
    
    def test_secrets_not_in_plaintext(self):
        """Test that secret values are never logged in plaintext."""
        # This is more of a reminder - actual implementation would need
        # to check logging configuration and output
        
        # Secret loading functions should never print actual values
        # They should use masking like: client_id[:4]...client_id[-4:]
        pass
    
    def test_mask_secret_utility(self):
        """Test the mask_secret utility function if it exists."""
        # Import the masking function from wherever it's defined
        # from stream_daemon.utils import mask_secret
        
        # Example test:
        # secret = "this_is_a_very_long_secret_key"
        # masked = mask_secret(secret)
        # assert "this" in masked  # Shows first 4
        # assert "_key" in masked  # Shows last 4
        # assert "very_long" not in masked  # Middle is hidden
        pass


@pytest.mark.integration
class TestSecretsManagerIntegration:
    """Integration tests for secrets manager connectivity."""
    
    def test_doppler_connectivity(self):
        """Test that Doppler API is accessible."""
        secret_manager = os.getenv('SECRETS_SECRET_MANAGER', '').lower()
        if secret_manager != 'doppler':
            pytest.skip("Doppler not configured")
        
        doppler_token = os.getenv('DOPPLER_TOKEN')
        assert doppler_token is not None, "DOPPLER_TOKEN not set"
        assert len(doppler_token) > 0, "DOPPLER_TOKEN is empty"
        
        # Try to load at least one secret to verify connectivity
        try:
            client_id = get_secret(
                'Twitch',
                'client_id',
                doppler_secret_env='SECRETS_DOPPLER_TWITCH_SECRET_NAME'
            )
            assert client_id is not None, "Could not fetch secret from Doppler - check token and permissions"
        except Exception as e:
            pytest.fail(f"Doppler connectivity test failed: {e}")
    
    def test_aws_connectivity(self):
        """Test that AWS Secrets Manager is accessible."""
        secret_manager = os.getenv('SECRETS_SECRET_MANAGER', '').lower()
        if secret_manager != 'aws':
            pytest.skip("AWS Secrets Manager not configured")
        
        # Verify AWS credentials are set
        aws_region = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION')
        assert aws_region is not None, "AWS_REGION not set"
        
        # Try to load at least one secret
        try:
            client_id = get_secret(
                'Twitch',
                'client_id',
                secret_name_env='SECRETS_AWS_TWITCH_SECRET_NAME'
            )
            assert client_id is not None, "Could not fetch secret from AWS - check credentials and permissions"
        except Exception as e:
            pytest.fail(f"AWS Secrets Manager connectivity test failed: {e}")
    
    def test_vault_connectivity(self):
        """Test that HashiCorp Vault is accessible."""
        secret_manager = os.getenv('SECRETS_SECRET_MANAGER', '').lower()
        if secret_manager != 'vault':
            pytest.skip("Vault not configured")
        
        vault_url = os.getenv('SECRETS_VAULT_URL')
        vault_token = os.getenv('SECRETS_VAULT_TOKEN')
        
        assert vault_url is not None, "SECRETS_VAULT_URL not set"
        assert vault_token is not None, "SECRETS_VAULT_TOKEN not set"
        
        # Try to load at least one secret
        try:
            client_id = get_secret(
                'Twitch',
                'client_id',
                secret_path_env='SECRETS_VAULT_TWITCH_SECRET_PATH'
            )
            assert client_id is not None, "Could not fetch secret from Vault - check URL, token, and permissions"
        except Exception as e:
            pytest.fail(f"Vault connectivity test failed: {e}")
