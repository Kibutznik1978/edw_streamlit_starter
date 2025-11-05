"""Reflex configuration for Data Editor POC."""

import reflex as rx

config = rx.Config(
    app_name="poc_data_editor",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
)
