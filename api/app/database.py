import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import psycopg2
import psycopg2.pool
import psycopg2.extras

from app.config import Settings

logger = logging.getLogger(__name__)


class Database:
    """Manages a connection pool to PostgreSQL and provides document CRUD operations."""
    
    def __init__(self, settings: Settings):
        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=2,
            maxconn=10,
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            dbname=settings.db_name,
        )
        logger.info("Database connection pool created")
    
    @contextmanager
    def get_connection(self):
        conn = self.pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self.pool.putconn(conn)
    
    def insert_document(self, filename: str, s3_key: str, content_type: str) -> dict:
        """Insert a new document record and return its metadata."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO documents (filename, s3_key, content_type)
                    VALUES (%s, %s, %s)
                    RETURNING id, filename, s3_key, content_type, created_at
                    """,
                    (filename, s3_key, content_type),
                )
                row = cur.fetchone()
        return dict(row)
    
    def get_all_documents(self) -> list:
        """Retrieve metadata for all documents."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, filename, s3_key, content_type, created_at FROM documents ORDER BY id"
                )
                rows = cur.fetchall()
        return [dict(row) for row in rows]
    
    def get_document_by_id(self, doc_id: int) -> Optional[dict]:
        """Retrieve metadata for a single document by its ID."""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT id, filename, s3_key, content_type, created_at FROM documents WHERE id = %s",
                    (doc_id,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return dict(row)
    
    def close(self):
        self.pool.closeall()
        logger.info("Database connection pool closed")
