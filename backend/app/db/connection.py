"""
app/db/connection.py
---------------------
PostgreSQL connection factory using psycopg (v3).

Works with both local PostgreSQL (sslmode=disable) and
CockroachDB Cloud (sslmode=require), controlled by DB_SSLMODE in .env.
"""

import psycopg
from psycopg.rows import dict_row
from flask import current_app


def get_connection():
 row_factory = dict_row,
    )