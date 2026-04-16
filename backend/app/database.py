import json
import os
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "backend" / "data"
DB_PATH = Path(os.getenv("NEUROLENS_DB_PATH", str(DATA_DIR / "neurolens.db")))


def get_connection():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                image_bytes BLOB NOT NULL,
                label TEXT NOT NULL,
                probabilities TEXT NOT NULL,
                classes TEXT NOT NULL,
                confidence REAL NOT NULL,
                confidence_gap REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        connection.commit()


def save_analysis(user_id, file_name, content_type, file_bytes, prediction_payload):
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO analyses (
                user_id,
                filename,
                content_type,
                image_bytes,
                label,
                probabilities,
                classes,
                confidence,
                confidence_gap
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                file_name,
                content_type,
                file_bytes,
                prediction_payload["label"],
                json.dumps(prediction_payload["probabilities"]),
                json.dumps(prediction_payload["classes"]),
                prediction_payload["confidence"],
                prediction_payload["confidence_gap"],
            ),
        )
        connection.commit()
        return cursor.lastrowid


def list_analyses(user_id, limit=10):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                user_id,
                filename,
                content_type,
                label,
                probabilities,
                classes,
                confidence,
                confidence_gap,
                created_at
            FROM analyses
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()
    return [serialize_analysis_row(row) for row in rows]


def get_analysis(analysis_id):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                id,
                user_id,
                filename,
                content_type,
                image_bytes,
                label,
                probabilities,
                classes,
                confidence,
                confidence_gap,
                created_at
            FROM analyses
            WHERE id = ?
            """,
            (analysis_id,),
        ).fetchone()
    return serialize_analysis_row(row) if row else None


def serialize_analysis_row(row):
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "filename": row["filename"],
        "content_type": row["content_type"],
        "image_bytes": row["image_bytes"] if "image_bytes" in row.keys() else None,
        "label": row["label"],
        "probabilities": json.loads(row["probabilities"]),
        "classes": json.loads(row["classes"]),
        "confidence": row["confidence"],
        "confidence_gap": row["confidence_gap"],
        "created_at": row["created_at"],
    }
