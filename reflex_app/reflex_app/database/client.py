"""Supabase client wrapper with authentication support."""

from supabase import create_client, Client
from typing import Optional
from ..config.database_config import db_config


class SupabaseClient:
    """Wrapper for Supabase client with authentication support."""

    _instance: Optional[Client] = None

    @classmethod
    def get_client(cls, jwt_token: Optional[str] = None) -> Client:
        """Get Supabase client instance.

        Args:
            jwt_token: Optional JWT token for authenticated requests

        Returns:
            Supabase client instance
        """
        if not cls._instance:
            cls._instance = create_client(
                db_config.supabase_url,
                db_config.supabase_anon_key
            )

        # Create new client with JWT if provided
        if jwt_token:
            auth_client = create_client(
                db_config.supabase_url,
                db_config.supabase_anon_key
            )
            # Attach JWT token for RLS enforcement
            auth_client.postgrest.auth(jwt_token)
            return auth_client

        return cls._instance

    @classmethod
    def reset(cls):
        """Reset client instance (for testing)."""
        cls._instance = None


def get_supabase_client(jwt_token: Optional[str] = None) -> Client:
    """Get Supabase client with optional JWT authentication.

    Args:
        jwt_token: Optional JWT token for authenticated requests

    Returns:
        Supabase client instance
    """
    return SupabaseClient.get_client(jwt_token)
