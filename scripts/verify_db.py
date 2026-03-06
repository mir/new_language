#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# requires-python = ">=3.12"
# ///

"""Verification and stats for the Greek B1 vocabulary database."""

import random
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "greek_b1.db"


def verify_database():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Total words
    cursor.execute("SELECT COUNT(*) FROM words")
    total = cursor.fetchone()[0]
    print(f"=== Database Statistics ===")
    print(f"Total words: {total}")
    print()

    # Words per part of speech
    print("--- By Part of Speech ---")
    cursor.execute("SELECT part_of_speech, COUNT(*) FROM words GROUP BY part_of_speech ORDER BY COUNT(*) DESC")
    for pos, count in cursor.fetchall():
        print(f"  {pos}: {count}")
    print()

    # Words per category
    print("--- By Category ---")
    cursor.execute("SELECT category, COUNT(*) FROM words WHERE category IS NOT NULL GROUP BY category ORDER BY COUNT(*) DESC")
    for cat, count in cursor.fetchall():
        print(f"  {cat}: {count}")
    cursor.execute("SELECT COUNT(*) FROM words WHERE category IS NULL")
    uncategorized = cursor.fetchone()[0]
    if uncategorized:
        print(f"  (uncategorized): {uncategorized}")
    print()

    # Nouns missing articles
    print("--- Quality Checks ---")
    cursor.execute("SELECT COUNT(*) FROM words WHERE part_of_speech = 'noun' AND article IS NULL")
    nouns_no_article = cursor.fetchone()[0]
    print(f"Nouns missing articles: {nouns_no_article}")
    if nouns_no_article > 0:
        cursor.execute("SELECT greek, english FROM words WHERE part_of_speech = 'noun' AND article IS NULL LIMIT 10")
        for greek, english in cursor.fetchall():
            print(f"  - {greek} ({english})")

    # Verb conjugation coverage
    cursor.execute("SELECT COUNT(*) FROM words WHERE part_of_speech = 'verb'")
    total_verbs = cursor.fetchone()[0]
    cursor.execute("""
        SELECT COUNT(DISTINCT w.id) FROM words w
        JOIN conjugations c ON w.id = c.word_id
        WHERE w.part_of_speech = 'verb'
    """)
    verbs_with_conj = cursor.fetchone()[0]
    print(f"Verbs with conjugations: {verbs_with_conj}/{total_verbs}")

    # Verbs missing conjugations
    cursor.execute("""
        SELECT w.greek FROM words w
        LEFT JOIN conjugations c ON w.id = c.word_id
        WHERE w.part_of_speech = 'verb' AND c.id IS NULL
        LIMIT 15
    """)
    missing = cursor.fetchall()
    if missing:
        print(f"Verbs missing conjugations (showing up to 15):")
        for (greek,) in missing:
            print(f"  - {greek}")

    # Total conjugation entries
    cursor.execute("SELECT COUNT(*) FROM conjugations")
    total_conj = cursor.fetchone()[0]
    print(f"Total conjugation entries: {total_conj}")

    # Conjugation coverage by tense
    cursor.execute("SELECT tense, COUNT(*) FROM conjugations GROUP BY tense")
    for tense, count in cursor.fetchall():
        print(f"  {tense}: {count}")
    print()

    # Spot check: random entries
    print("--- Spot Check (5 random entries) ---")
    cursor.execute("SELECT id, greek, english, part_of_speech, article, category FROM words ORDER BY RANDOM() LIMIT 5")
    for row in cursor.fetchall():
        word_id, greek, english, pos, article, category = row
        info = f"{greek} = {english} [{pos}]"
        if article:
            info += f" (article: {article})"
        if category:
            info += f" (category: {category})"

        # Check conjugations if verb
        if pos == "verb":
            cursor.execute("SELECT tense, person, conjugation FROM conjugations WHERE word_id = ? ORDER BY tense, person", (word_id,))
            conjs = cursor.fetchall()
            if conjs:
                info += f"\n    Conjugations ({len(conjs)} forms):"
                for tense, person, form in conjs[:6]:
                    info += f"\n      {tense} {person}: {form}"
                if len(conjs) > 6:
                    info += f"\n      ... and {len(conjs) - 6} more"
        print(f"  {info}")
    print()

    # Example sentences
    cursor.execute("SELECT COUNT(*) FROM examples")
    total_examples = cursor.fetchone()[0]
    print(f"Total example sentences: {total_examples}")

    conn.close()


if __name__ == "__main__":
    verify_database()
