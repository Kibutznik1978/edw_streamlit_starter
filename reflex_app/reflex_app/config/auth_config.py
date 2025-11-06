"""Authentication configuration for Reflex application."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AuthConfig:
    """Authentication configuration."""

    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")

    # JWT
    jwt_algorithm: str = "HS256"
    jwt_expiration: int = 3600  # 1 hour
    jwt_refresh_threshold: int = 300  # 5 minutes

    # Cookies
    cookie_name: str = "jwt_token"
    cookie_max_age: int = 3600  # 1 hour
    cookie_secure: bool = False  # Set to True in production with HTTPS
    cookie_http_only: bool = True  # No JS access
    cookie_same_site: str = "lax"  # CSRF protection (lax for dev, strict for prod)

    # Session
    session_timeout: int = 3600  # 1 hour
    remember_me_duration: int = 604800  # 7 days

    def validate(self) -> bool:
        """Validate configuration."""
        if not self.supabase_url:
            raise ValueError("SUPABASE_URL not set in .env file")
        if not self.supabase_anon_key:
            raise ValueError("SUPABASE_ANON_KEY not set in .env file")
        return True


# Global configuration instance
auth_config = AuthConfig()

try:
    auth_config.validate()
    print("✅ Authentication configuration loaded successfully")
except ValueError as e:
    print(f"⚠️  Authentication configuration warning: {e}")
    print("   Some features may not work until .env is configured")
