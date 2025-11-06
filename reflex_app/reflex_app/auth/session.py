"""JWT session management utilities."""

import json
import base64
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class JWTSession:
    """JWT session management utilities."""

    @staticmethod
    def decode_payload(token: str) -> Dict[str, Any]:
        """Decode JWT payload without verification.

        Args:
            token: JWT token string

        Returns:
            Dictionary of JWT claims
        """
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return {}

            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding

            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception as e:
            print(f"JWT decode error: {e}")
            return {}

    @staticmethod
    def is_expired(token: str) -> bool:
        """Check if JWT is expired.

        Args:
            token: JWT token string

        Returns:
            True if expired, False otherwise
        """
        claims = JWTSession.decode_payload(token)
        exp = claims.get('exp', 0)
        return datetime.now().timestamp() > exp

    @staticmethod
    def needs_refresh(token: str, threshold_seconds: int = 300) -> bool:
        """Check if JWT should be refreshed (within threshold of expiry).

        Args:
            token: JWT token string
            threshold_seconds: Time before expiry to trigger refresh (default: 5 minutes)

        Returns:
            True if token needs refresh, False otherwise
        """
        claims = JWTSession.decode_payload(token)
        exp = claims.get('exp', 0)
        time_until_expiry = exp - datetime.now().timestamp()
        return 0 < time_until_expiry < threshold_seconds

    @staticmethod
    def get_user_id(token: str) -> Optional[str]:
        """Extract user ID from JWT.

        Args:
            token: JWT token string

        Returns:
            User ID or None
        """
        claims = JWTSession.decode_payload(token)
        return claims.get('sub')

    @staticmethod
    def get_user_email(token: str) -> Optional[str]:
        """Extract user email from JWT.

        Args:
            token: JWT token string

        Returns:
            User email or None
        """
        claims = JWTSession.decode_payload(token)
        return claims.get('email')

    @staticmethod
    def get_user_role(token: str) -> str:
        """Extract user role from JWT.

        Args:
            token: JWT token string

        Returns:
            User role (defaults to 'user')
        """
        claims = JWTSession.decode_payload(token)
        # POC 4 finding: use app_role, not user_role
        return claims.get('app_role', 'user')

    @staticmethod
    def get_expiration_time(token: str) -> Optional[datetime]:
        """Get JWT expiration as datetime.

        Args:
            token: JWT token string

        Returns:
            Expiration datetime or None
        """
        claims = JWTSession.decode_payload(token)
        exp = claims.get('exp')
        if exp:
            return datetime.fromtimestamp(exp)
        return None
