import logging
import os

logging.basicConfig(level=logging.DEBUG)

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

DB_USER = os.environ.get("POSTGRES_USER", "NOT_SET")
DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "NOT_SET")
DB_HOST = os.environ.get("POSTGRES_HOST", "NOT_SET")
DB_PORT = int(os.environ.get("POSTGRES_PORT", 42))
DB_DATABASE = os.environ.get("POSTGRES_DB", "NOT_SET")

TENACITY_DELAY = 1
