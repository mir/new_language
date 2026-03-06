#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# requires-python = ">=3.12"
# ///

"""Creates the Greek B1 vocabulary SQLite database with schema."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "greek_b1.db"


def create_database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE words (
            id INTEGER PRIMARY KEY,
            greek TEXT NOT NULL,
            english TEXT NOT NULL,
            part_of_speech TEXT NOT NULL,
            article TEXT,
            category TEXT,
            notes TEXT
        );

        CREATE TABLE conjugations (
            id INTEGER PRIMARY KEY,
            word_id INTEGER NOT NULL REFERENCES words(id),
            tense TEXT NOT NULL,
            person TEXT NOT NULL,
            conjugation TEXT NOT NULL
        );

        CREATE TABLE examples (
            id INTEGER PRIMARY KEY,
            word_id INTEGER NOT NULL REFERENCES words(id),
            greek_sentence TEXT NOT NULL,
            english_sentence TEXT NOT NULL
        );

        CREATE INDEX idx_words_pos ON words(part_of_speech);
        CREATE INDEX idx_words_category ON words(category);
        CREATE INDEX idx_conjugations_word_id ON conjugations(word_id);
        CREATE INDEX idx_examples_word_id ON examples(word_id);
    """)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH}")


if __name__ == "__main__":
    create_database()
