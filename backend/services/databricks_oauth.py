"""
Databricks OAuth Token Management
Automatic token rotation using Databricks Workspace API
"""
import os
import time
import logging
from typing import Optional
from datetime import datetime, timedelta
import jwt

logger = logging.getLogger(__name__)


class DatabricksOAuthManager:
    """
    Manages Databricks OAuth tokens with automatic rotation
    """

    def __init__(self):
        self.oauth_token = os.getenv('DATABRICKS_OAUTH_TOKEN')
        self.workspace_url = os.getenv('DATABRICKS_HOST', 'https://fe-vm-hls-amer.cloud.databricks.com')
        self._cached_token = None
        self._token_expiry = None

    def get_token(self) -> str:
        """
        Get valid OAuth token, refreshing if needed

        Returns:
            Valid OAuth token string
        """
        # Check if cached token is still valid
        if self._cached_token and self._token_expiry:
            if datetime.now() < self._token_expiry - timedelta(minutes=5):
                # Token still valid for at least 5 more minutes
                return self._cached_token

        # Decode current token to check expiry
        try:
            decoded = jwt.decode(
                self.oauth_token,
                options={"verify_signature": False}  # We trust the token from env
            )

            exp_timestamp = decoded.get('exp')
            if exp_timestamp:
                expiry = datetime.fromtimestamp(exp_timestamp)

                # Check if token is still valid
                if datetime.now() < expiry - timedelta(minutes=5):
                    self._cached_token = self.oauth_token
                    self._token_expiry = expiry
                    logger.info(f"OAuth token valid until {expiry}")
                    return self.oauth_token
                else:
                    logger.warning(f"OAuth token expired at {expiry}, needs refresh")
                    return self._refresh_token()
            else:
                # No expiry in token, use it as-is
                self._cached_token = self.oauth_token
                return self.oauth_token

        except Exception as e:
            logger.error(f"Error decoding OAuth token: {e}")
            # Return current token if we can't decode
            return self.oauth_token

    def _refresh_token(self) -> str:
        """
        Refresh OAuth token using Databricks Workspace API

        NOTE: For OAuth token refresh, you would typically need to:
        1. Use the Databricks CLI to get a new token
        2. Or implement OAuth2 refresh flow with your OAuth provider

        For now, we'll log a warning and return the current token.
        In production, implement proper token refresh logic.
        """
        logger.warning("OAuth token needs refresh. Please update DATABRICKS_OAUTH_TOKEN in .env")

        # In a production setup, you would:
        # 1. Call Databricks OAuth endpoint to refresh
        # 2. Update the token in secure storage
        # 3. Return the new token

        # For development, we return the current token
        # User should manually refresh via Databricks CLI or UI
        return self.oauth_token

    def get_headers(self) -> dict:
        """
        Get authorization headers for Databricks API calls

        Returns:
            Dictionary with Authorization header
        """
        token = self.get_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

    def is_token_valid(self) -> bool:
        """
        Check if current token is valid

        Returns:
            True if token is valid, False otherwise
        """
        try:
            decoded = jwt.decode(
                self.oauth_token,
                options={"verify_signature": False}
            )

            exp_timestamp = decoded.get('exp')
            if exp_timestamp:
                expiry = datetime.fromtimestamp(exp_timestamp)
                return datetime.now() < expiry
            return True  # No expiry means token doesn't expire

        except Exception as e:
            logger.error(f"Error validating token: {e}")
            return False

    def get_token_info(self) -> dict:
        """
        Get information about current token

        Returns:
            Dictionary with token information
        """
        try:
            decoded = jwt.decode(
                self.oauth_token,
                options={"verify_signature": False}
            )

            exp_timestamp = decoded.get('exp')
            iat_timestamp = decoded.get('iat')

            info = {
                'subject': decoded.get('sub'),
                'client_id': decoded.get('client_id'),
                'scopes': decoded.get('scope', '').split(' '),
                'issuer': decoded.get('iss'),
                'audience': decoded.get('aud'),
            }

            if exp_timestamp:
                expiry = datetime.fromtimestamp(exp_timestamp)
                info['expires_at'] = expiry.isoformat()
                info['expires_in_minutes'] = int((expiry - datetime.now()).total_seconds() / 60)
                info['is_valid'] = datetime.now() < expiry
            else:
                info['expires_at'] = None
                info['expires_in_minutes'] = None
                info['is_valid'] = True

            if iat_timestamp:
                info['issued_at'] = datetime.fromtimestamp(iat_timestamp).isoformat()

            return info

        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            return {'error': str(e)}


# Global OAuth manager instance
_oauth_manager = None


def get_oauth_manager() -> DatabricksOAuthManager:
    """
    Get global OAuth manager instance (singleton)

    Returns:
        DatabricksOAuthManager instance
    """
    global _oauth_manager
    if _oauth_manager is None:
        _oauth_manager = DatabricksOAuthManager()
    return _oauth_manager


def get_databricks_token() -> str:
    """
    Convenience function to get valid Databricks token

    Returns:
        Valid OAuth token string
    """
    manager = get_oauth_manager()
    return manager.get_token()


def get_databricks_headers() -> dict:
    """
    Convenience function to get Databricks API headers

    Returns:
        Dictionary with Authorization header
    """
    manager = get_oauth_manager()
    return manager.get_headers()


# Example usage
if __name__ == '__main__':
    # Test token management
    manager = get_oauth_manager()

    print("Token Info:")
    info = manager.get_token_info()
    for key, value in info.items():
        print(f"  {key}: {value}")

    print(f"\nToken valid: {manager.is_token_valid()}")
    print(f"Token: {manager.get_token()[:50]}...")
