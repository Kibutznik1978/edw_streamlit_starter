"""Database configuration for Reflex application."""

from .auth_config import auth_config


class DatabaseConfig:
    """Database configuration."""

    supabase_url = auth_config.supabase_url
    supabase_anon_key = auth_config.supabase_anon_key

    # Connection settings
    max_connections = 10
    connection_timeout = 30  # seconds

    # Query settings
    query_timeout = 10  # seconds
    max_retries = 3


# Global configuration instance
db_config = DatabaseConfig()
