"""
Tests for AWS Secrets Manager integration
"""
import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from mcp_server.secrets_manager import (
    SecretsManager,
    get_secrets_manager,
    get_database_config,
    get_s3_bucket
)


class TestSecretsManager:
    """Test SecretsManager class"""

    def test_initialization(self):
        """Test SecretsManager initializes correctly"""
        with patch('boto3.client'):
            sm = SecretsManager(region_name='us-west-2')
            assert sm.region_name == 'us-west-2'
            assert sm.client is not None

    def test_get_secret_success(self):
        """Test successful secret retrieval"""
        # Mock boto3 client
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"key": "value", "password": "secret123"}'
        }

        with patch('boto3.client', return_value=mock_client):
            sm = SecretsManager()
            secret = sm.get_secret('test-secret')

            assert secret == {'key': 'value', 'password': 'secret123'}
            mock_client.get_secret_value.assert_called_once_with(
                SecretId='test-secret'
            )

    def test_get_secret_not_found(self):
        """Test handling of non-existent secret"""
        mock_client = MagicMock()
        mock_client.exceptions.ResourceNotFoundException = Exception
        mock_client.get_secret_value.side_effect = (
            mock_client.exceptions.ResourceNotFoundException()
        )

        with patch('boto3.client', return_value=mock_client):
            sm = SecretsManager()

            with pytest.raises(ValueError, match="not found"):
                sm.get_secret('nonexistent-secret')

    def test_get_database_credentials(self):
        """Test retrieving database credentials"""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"host": "localhost", "user": "postgres", "password": "secret", "database": "nba", "port": 5432}'
        }

        with patch('boto3.client', return_value=mock_client):
            sm = SecretsManager()
            creds = sm.get_database_credentials('production')

            assert creds['host'] == 'localhost'
            assert creds['user'] == 'postgres'
            assert creds['password'] == 'secret'
            assert creds['database'] == 'nba'
            assert creds['port'] == 5432

    def test_get_s3_config(self):
        """Test retrieving S3 configuration"""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"bucket": "my-bucket", "region": "us-east-1"}'
        }

        with patch('boto3.client', return_value=mock_client):
            sm = SecretsManager()
            config = sm.get_s3_config('production')

            assert config['bucket'] == 'my-bucket'
            assert config['region'] == 'us-east-1'

    def test_secret_caching(self):
        """Test that secrets are cached"""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"key": "value"}'
        }

        with patch('boto3.client', return_value=mock_client):
            sm = SecretsManager()

            # First call
            secret1 = sm.get_secret('test-secret')

            # Second call (should use cache)
            secret2 = sm.get_secret('test-secret')

            # Should only call AWS once
            assert mock_client.get_secret_value.call_count == 1

            # Clear cache
            sm.clear_cache()

            # Third call (fresh)
            secret3 = sm.get_secret('test-secret')

            # Should have called AWS twice now
            assert mock_client.get_secret_value.call_count == 2

    def test_rotate_secret(self):
        """Test secret rotation"""
        mock_client = MagicMock()
        mock_client.rotate_secret.return_value = {'ARN': 'test-arn'}

        with patch('boto3.client', return_value=mock_client):
            sm = SecretsManager()
            result = sm.rotate_secret('test-secret')

            assert result is True
            mock_client.rotate_secret.assert_called_once_with(
                SecretId='test-secret'
            )

    def test_rotate_secret_failure(self):
        """Test secret rotation failure"""
        mock_client = MagicMock()
        mock_client.rotate_secret.side_effect = Exception("Rotation failed")

        with patch('boto3.client', return_value=mock_client):
            sm = SecretsManager()
            result = sm.rotate_secret('test-secret')

            assert result is False


class TestHelperFunctions:
    """Test helper functions"""

    def test_get_database_config_local_mode(self):
        """Test get_database_config with local credentials"""
        with patch.dict(os.environ, {
            'USE_LOCAL_CREDENTIALS': 'true',
            'DB_HOST': 'localhost',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass',
            'DB_NAME': 'testdb',
            'DB_PORT': '5433'
        }):
            config = get_database_config()

            assert config['host'] == 'localhost'
            assert config['user'] == 'testuser'
            assert config['password'] == 'testpass'
            assert config['database'] == 'testdb'
            assert config['port'] == 5433

    def test_get_database_config_secrets_manager_mode(self):
        """Test get_database_config with Secrets Manager"""
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"host": "aws-host", "user": "awsuser", "password": "awspass", "database": "awsdb", "port": 5432}'
        }

        with patch('boto3.client', return_value=mock_client):
            with patch.dict(os.environ, {'USE_LOCAL_CREDENTIALS': 'false'}):
                config = get_database_config()

                assert config['host'] == 'aws-host'
                assert config['user'] == 'awsuser'
                assert config['password'] == 'awspass'

    def test_get_s3_bucket_local_mode(self):
        """Test get_s3_bucket with local credentials"""
        with patch.dict(os.environ, {
            'USE_LOCAL_CREDENTIALS': 'true',
            'S3_BUCKET': 'local-bucket'
        }):
            bucket = get_s3_bucket()
            assert bucket == 'local-bucket'

    def test_get_s3_bucket_secrets_manager_mode(self):
        """Test get_s3_bucket with Secrets Manager"""
        mock_sm = MagicMock()
        mock_sm.get_s3_config.return_value = {'bucket': 'aws-bucket'}

        with patch('mcp_server.secrets_manager.get_secrets_manager', return_value=mock_sm):
            with patch.dict(os.environ, {'USE_LOCAL_CREDENTIALS': 'false'}):
                bucket = get_s3_bucket()
                assert bucket == 'aws-bucket'


class TestIntegration:
    """Integration tests (require AWS credentials)"""

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('RUN_INTEGRATION_TESTS'),
        reason="Integration tests disabled (set RUN_INTEGRATION_TESTS=1)"
    )
    def test_real_secrets_manager_connection(self):
        """Test actual connection to AWS Secrets Manager"""
        sm = SecretsManager()

        # List secrets to verify connection
        response = sm.client.list_secrets(MaxResults=1)
        assert 'SecretList' in response

    @pytest.mark.integration
    @pytest.mark.skipif(
        not os.getenv('RUN_INTEGRATION_TESTS'),
        reason="Integration tests disabled"
    )
    def test_real_secret_retrieval(self):
        """Test retrieving actual secret from AWS"""
        # This test requires nba-mcp/production/database secret to exist
        try:
            config = get_database_config()
            assert 'host' in config
            assert 'user' in config
            assert 'password' in config
            print("✅ Successfully retrieved real secrets from AWS")
        except ValueError as e:
            pytest.skip(f"Secret not found (expected for first-time setup): {e}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

