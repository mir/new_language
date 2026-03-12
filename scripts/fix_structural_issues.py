# /// script
# requires-python = ">=3.12"
# ///
"""Fix structural issues in the Greek B1 vocabulary database.

Issue 1: Merge 44 near-duplicate noun pairs (bare word + article version)
Issue 2: Prepend article to 7 nouns missing it in the greek column
Issue 3: Parse 127 entries with (m)/(f)/(n) gender markers
"""

import sqlite3
import re
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "greek_b1.db"

GENDER_MAP = {
    "(m)": "ο",
    "(f)": "η",
    "(n)": "το",
}


def fix_issue1_merge_duplicates(cur: sqlite3.Cursor) -> int:
    """Merge near-duplicate noun pairs: bare word vs article + word.

    Keep the version WITH the article, delete the bare one.
    Reassign FK references before deleting.
    """
    print("\n=== Issue 1: Merge near-duplicate noun pairs ===")

    # Find pairs where bare.greek matches the suffix of articled.greek
    cur.execute("""
        SELECT bare.id AS bare_id, bare.greek AS bare_greek,
               articled.id AS articled_id, articled.greek AS articled_greek
        FROM words bare
        JOIN words articled ON (
            articled.greek = 'ο ' || bare.greek
            OR articled.greek = 'η ' || bare.greek
            OR articled.greek = 'το ' || bare.greek
        )
        WHERE bare.part_of_speech = 'noun'
          AND bare.greek NOT LIKE 'ο %'
          AND bare.greek NOT LIKE 'η %'
          AND bare.greek NOT LIKE 'το %'
        ORDER BY bare.id
    """)
    pairs = cur.fetchall()

    if not pairs:
        print("  No duplicate pairs found.")
        return 0

    count = 0
    for bare_id, bare_greek, articled_id, articled_greek in pairs:
        # Reassign conjugations
        cur.execute("UPDATE conjugations SET word_id = ? WHERE word_id = ?",
                    (articled_id, bare_id))
        conj_moved = cur.rowcount

        # Reassign examples
        cur.execute("UPDATE examples SET word_id = ? WHERE word_id = ?",
                    (articled_id, bare_id))
        ex_moved = cur.rowcount

        # Delete bare duplicate
        cur.execute("DELETE FROM words WHERE id = ?", (bare_id,))

        refs = []
        if conj_moved:
            refs.append(f"{conj_moved} conjugations")
        if ex_moved:
            refs.append(f"{ex_moved} examples")
        ref_str = f" (reassigned {', '.join(refs)})" if refs else ""

        print(f"  Merged: '{bare_greek}' (id {bare_id}) -> '{articled_greek}' (id {articled_id}){ref_str}")
        count += 1

    print(f"  Total merged: {count} pairs")
    return count


def fix_issue2_prepend_article(cur: sqlite3.Cursor) -> int:
    """Prepend article to nouns that have article column set but not in greek column."""
    print("\n=== Issue 2: Prepend article to nouns missing it in greek column ===")

    cur.execute("""
        SELECT id, greek, article
        FROM words
        WHERE part_of_speech = 'noun'
          AND article IS NOT NULL AND article != ''
          AND greek NOT LIKE 'ο %'
          AND greek NOT LIKE 'η %'
          AND greek NOT LIKE 'το %'
          AND greek NOT LIKE 'τα %'
          AND greek NOT LIKE 'οι %'
          AND greek NOT LIKE 'τους %'
          AND greek NOT LIKE '%(m)%'
          AND greek NOT LIKE '%(f)%'
          AND greek NOT LIKE '%(n)%'
    """)
    rows = cur.fetchall()

    if not rows:
        print("  No nouns to fix.")
        return 0

    count = 0
    for word_id, greek, article in rows:
        new_greek = f"{article} {greek}"
        cur.execute("UPDATE words SET greek = ? WHERE id = ?", (new_greek, word_id))
        print(f"  Updated: '{greek}' -> '{new_greek}' (id {word_id})")
        count += 1

    print(f"  Total updated: {count}")
    return count


def fix_issue3_gender_markers(cur: sqlite3.Cursor) -> int:
    """Parse (m)/(f)/(n) gender markers, set article, strip marker, prepend article."""
    print("\n=== Issue 3: Parse gender markers (m)/(f)/(n) ===")

    cur.execute("""
        SELECT id, greek, article
        FROM words
        WHERE greek LIKE '%(m)%'
           OR greek LIKE '%(f)%'
           OR greek LIKE '%(n)%'
    """)
    rows = cur.fetchall()

    if not rows:
        print("  No entries with gender markers found.")
        return 0

    count = 0
    for word_id, greek, existing_article in rows:
        # Find the gender marker
        match = re.search(r'\(([mfn])\)', greek)
        if not match:
            continue

        marker = f"({match.group(1)})"
        article = GENDER_MAP[marker]

        # Strip the marker and clean up whitespace
        cleaned = greek.replace(marker, "").strip()
        # Remove any double spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)

        # Prepend article if not already present
        if not cleaned.startswith(f"{article} "):
            new_greek = f"{article} {cleaned}"
        else:
            new_greek = cleaned

        cur.execute("UPDATE words SET greek = ?, article = ? WHERE id = ?",
                    (new_greek, article, word_id))
        print(f"  Updated: '{greek}' -> '{new_greek}' (article='{article}', id {word_id})")
        count += 1

    print(f"  Total updated: {count}")
    return count


def main():
    print(f"Database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Get initial counts
    cur.execute("SELECT count(*) FROM words")
    initial_words = cur.fetchone()[0]
    print(f"Initial word count: {initial_words}")

    try:
        # Run all fixes in a single transaction
        fix_issue1_merge_duplicates(cur)
        fix_issue2_prepend_article(cur)
        fix_issue3_gender_markers(cur)

        conn.commit()
        print("\n=== All changes committed successfully ===")

        # Final counts
        cur.execute("SELECT count(*) FROM words")
        final_words = cur.fetchone()[0]
        print(f"Final word count: {final_words} (was {initial_words}, removed {initial_words - final_words})")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        print("All changes rolled back.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
