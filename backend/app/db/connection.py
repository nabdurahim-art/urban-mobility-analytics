"""PostgreSQL connection factory using psycopg 3."""

import psycopg
from flask import current_app
from psycopg.rows import dict_row


def get_connection():
    return psycopg.connect(
        host=current_app.config["DB_HOST"],
        port=current_app.config["DB_PORT"],
        dbname=current_app.config["DB_NAME"],
        user=current_app.config["DB_USER"],
        password=current_app.config["DB_PASSWORD"],
        sslmode=current_app.config.get("DB_SSLMODE", "verify-full"),
        row_factory=dict_row,
    )
