"""Reflex configuration for JWT Auth POC."""

import reflex as rx

config = rx.Config(
    app_name="poc_jwt_auth",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
)
