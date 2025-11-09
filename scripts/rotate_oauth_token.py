#!/usr/bin/env python3
"""
Databricks OAuth Token Rotation Script

This script handles automatic OAuth token rotation for Databricks workspace.
It can use either:
1. Databricks CLI (recommended)
2. OAuth2 refresh token flow (if refresh token is available)
3. Service Principal M2M flow (for production)
"""

import os
import sys
import json
import subprocess
import jwt
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any


class DatabricksTokenRotator:
    """Manages Databricks OAuth token rotation"""

    def __init__(self, env_file: str = ".env"):
        self.env_file = Path(env_file)
        self.workspace_url = os.getenv(
            'DATABRICKS_HOST',
            'https://fe-vm-hls-amer.cloud.databricks.com'
        )
        self.current_token = os.getenv('DATABRICKS_OAUTH_TOKEN')

    def get_token_info(self) -> Dict[str, Any]:
        """Get information about current token"""
        try:
            decoded = jwt.decode(
                self.current_token,
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
                info['expires_in_minutes'] = int(
                    (expiry - datetime.now()).total_seconds() / 60
                )
                info['is_expired'] = datetime.now() >= expiry

            if iat_timestamp:
                info['issued_at'] = datetime.fromtimestamp(iat_timestamp).isoformat()

            return info

        except Exception as e:
            return {'error': str(e)}

    def is_token_expired(self) -> bool:
        """Check if token is expired or will expire soon (within 5 minutes)"""
        info = self.get_token_info()

        if 'error' in info:
            print(f"⚠️  Error checking token: {info['error']}")
            return True

        expires_in_minutes = info.get('expires_in_minutes', 0)

        if expires_in_minutes <= 5:
            print(f"⚠️  Token expires in {expires_in_minutes} minutes")
            return True

        print(f"✅ Token valid for {expires_in_minutes} minutes")
        return False

    def rotate_token_via_cli(self) -> Optional[str]:
        """
        Rotate token using Databricks CLI
        This is the recommended method for development
        """
        print("🔄 Rotating token via Databricks CLI...")

        # Check if databricks CLI is installed
        try:
            subprocess.run(
                ['databricks', '--version'],
                capture_output=True,
                check=True
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ Databricks CLI not found")
            print("   Install: pip install databricks-cli")
            return None

        # Get new token
        try:
            # First, ensure we're logged in
            result = subprocess.run(
                ['databricks', 'auth', 'token', '--host', self.workspace_url],
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                print("⚠️  Not logged in. Running login...")
                subprocess.run(
                    ['databricks', 'auth', 'login', '--host', self.workspace_url],
                    check=True
                )

                # Try again
                result = subprocess.run(
                    ['databricks', 'auth', 'token', '--host', self.workspace_url],
                    capture_output=True,
                    text=True,
                    check=True
                )

            # Parse token from output
            output = result.stdout.strip()
            if output.startswith('eyJ'):  # JWT tokens start with eyJ
                return output
            else:
                # Try to parse JSON response
                try:
                    data = json.loads(output)
                    return data.get('access_token')
                except json.JSONDecodeError:
                    print(f"❌ Unexpected output: {output}")
                    return None

        except subprocess.CalledProcessError as e:
            print(f"❌ Error getting token: {e}")
            return None

    def update_env_file(self, new_token: str) -> bool:
        """Update .env file with new token"""
        try:
            if not self.env_file.exists():
                print(f"❌ .env file not found: {self.env_file}")
                return False

            # Read current .env
            with open(self.env_file, 'r') as f:
                lines = f.readlines()

            # Update token line
            updated = False
            for i, line in enumerate(lines):
                if line.startswith('DATABRICKS_OAUTH_TOKEN='):
                    lines[i] = f'DATABRICKS_OAUTH_TOKEN={new_token}\n'
                    updated = True
                    break

            if not updated:
                # Add token if not found
                lines.append(f'DATABRICKS_OAUTH_TOKEN={new_token}\n')

            # Write back
            with open(self.env_file, 'w') as f:
                f.writelines(lines)

            print(f"✅ Updated {self.env_file}")
            return True

        except Exception as e:
            print(f"❌ Error updating .env: {e}")
            return False

    def rotate(self) -> bool:
        """Main rotation logic"""
        print("=" * 60)
        print("🔐 Databricks OAuth Token Rotation")
        print("=" * 60)
        print("")

        # Check current token
        print("📊 Current Token Status:")
        info = self.get_token_info()
        for key, value in info.items():
            if key != 'scopes':
                print(f"   {key}: {value}")
        print("")

        # Check if rotation is needed
        if not self.is_token_expired():
            print("✅ Token is still valid. No rotation needed.")
            return True

        print("")
        print("🔄 Token expired or expiring soon. Rotating...")
        print("")

        # Rotate via CLI
        new_token = self.rotate_token_via_cli()

        if not new_token:
            print("❌ Token rotation failed")
            print("")
            print("Manual rotation:")
            print(f"   1. Run: databricks auth login --host {self.workspace_url}")
            print(f"   2. Run: databricks auth token --host {self.workspace_url}")
            print(f"   3. Copy token to .env DATABRICKS_OAUTH_TOKEN")
            return False

        # Verify new token
        try:
            decoded = jwt.decode(new_token, options={"verify_signature": False})
            exp_timestamp = decoded.get('exp')
            if exp_timestamp:
                expiry = datetime.fromtimestamp(exp_timestamp)
                print(f"✅ New token valid until: {expiry.isoformat()}")
        except Exception as e:
            print(f"⚠️  Could not verify new token: {e}")

        # Update .env
        if self.update_env_file(new_token):
            print("")
            print("🎉 Token rotation successful!")
            print("")
            print("⚠️  IMPORTANT: Restart your backend server to use the new token")
            print("   pkill -f 'python main.py' && python main.py")
            return True
        else:
            print("")
            print("⚠️  Token obtained but failed to update .env")
            print(f"   Manually add this token to {self.env_file}:")
            print(f"   DATABRICKS_OAUTH_TOKEN={new_token}")
            return False


def main():
    """Main entry point"""
    rotator = DatabricksTokenRotator()
    success = rotator.rotate()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
