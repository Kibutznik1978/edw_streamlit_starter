"""Reflex configuration for File Upload POC."""

import reflex as rx

config = rx.Config(
    app_name="poc_file_upload",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
)
