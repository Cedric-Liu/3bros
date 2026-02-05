"""
Dependencies - shared state to avoid circular imports
"""
from .db.models import Database

# Global database instance, set during app startup
_db: Database = None


def set_db(db: Database):
    global _db
    _db = db


def get_db() -> Database:
    return _db
