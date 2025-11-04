"""Reflex configuration for Aero Crew Data Analyzer."""

import reflex as rx

config = rx.Config(
    app_name="reflex_app",
    db_url="sqlite:///reflex.db",  # Local dev database, will be replaced with Supabase
    env=rx.Env.DEV,
)
