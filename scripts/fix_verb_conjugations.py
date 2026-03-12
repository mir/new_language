#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["requests<3", "beautifulsoup4"]
# requires-python = ">=3.12"
# ///

"""Fix verbs with incomplete conjugations in the Greek B1 database.

Finds verbs with fewer than 18 conjugation forms (3 tenses x 6 persons),
scrapes missing tenses from Cooljugator, and inserts them.
Also cleans up periphrastic verb forms (να έχω, θα είμαι) that duplicate
base verbs.
"""

import sqlite3
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent.parent / "db" / "greek_b1.db"
CACHE_DIR = Path(__file__).parent.parent / "db" / "conjugation_cache"
BASE_URL = "https://cooljugator.com/gr/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Cooljugator cell ID prefixes mapped to our tense names and person codes.
TENSE_ID_MAP = {
    "present": {
        "infinitive0": "1s",
        "present2": "2s",
        "present3": "3s",
        "present4": "1p",
        "present5": "2p",
        "present6": "3p",
    },
    "future": {
        f"future{i}": p
        for i, p in [(1, "1s"), (2, "2s"), (3, "3s"), (4, "1p"), (5, "2p"), (6, "3p")]
    },
    "past": {
        f"pastperfect{i}": p
        for i, p in [(1, "1s"), (2, "2s"), (3, "3s"), (4, "1p"), (5, "2p"), (6, "3p")]
    },
}

# Fallback IDs for irregular verbs (e.g. είμαι, έχω) that use pastimperfect
# instead of pastperfect on Cooljugator.
PAST_FALLBACK_IDS = {
    f"pastimperfect{i}": p
    for i, p in [(1, "1s"), (2, "2s"), (3, "3s"), (4, "1p"), (5, "2p"), (6, "3p")]
}


def fetch_conjugation_page(verb: str) -> str | None:
    """Fetch the conjugation page, using cache if available."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = urllib.parse.quote(verb, safe="")
    cache_file = CACHE_DIR / f"{safe_name}.html"

    if cache_file.exists():
        print(f"    (using cached page)")
        return cache_file.read_text(encoding="utf-8")

    url = BASE_URL + urllib.parse.quote(verb)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            cache_file.write_text(resp.text, encoding="utf-8")
            return resp.text
        elif resp.status_code == 404:
            print(f"    Not found on Cooljugator: {verb}")
            return None
        else:
            print(f"    HTTP {resp.status_code} for {verb}")
            return None
    except requests.RequestException as e:
        print(f"    Request error for {verb}: {e}")
        return None


def parse_conjugations(html: str) -> dict[str, dict[str, str]]:
    """Parse conjugation tables from Cooljugator HTML.

    Handles irregular verbs that use pastimperfect instead of pastperfect,
    and generates future forms with θα prefix when no future tense is found.
    """
    soup = BeautifulSoup(html, "html.parser")
    results: dict[str, dict[str, str]] = {}

    for tense_name, id_to_person in TENSE_ID_MAP.items():
        conjugations: dict[str, str] = {}
        for cell_id, person in id_to_person.items():
            el = soup.find("div", id=cell_id)
            if el:
                form = el.get("data-default", "").strip()
                if form:
                    conjugations[person] = form
        if conjugations:
            results[tense_name] = conjugations

    # Fallback: if no past tense found via pastperfect IDs, try pastimperfect
    # (used by irregular verbs like είμαι, έχω on Cooljugator)
    if "past" not in results:
        conjugations = {}
        for cell_id, person in PAST_FALLBACK_IDS.items():
            el = soup.find("div", id=cell_id)
            if el:
                form = el.get("data-default", "").strip()
                if form:
                    conjugations[person] = form
        if conjugations:
            print(f"    (using pastimperfect fallback for past tense)")
            results["past"] = conjugations

    # Fallback: if no future tense found, construct it from present with θα prefix
    # In Modern Greek, many verbs form the future with θα + present form
    if "future" not in results and "present" in results:
        conjugations = {}
        for person, form in results["present"].items():
            conjugations[person] = f"θα {form}"
        print(f"    (constructing future tense with θα + present)")
        results["future"] = conjugations

    return results


def get_verb_stem(greek: str) -> str:
    """Extract the base verb form for Cooljugator lookup."""
    word = greek.strip()
    for prefix in ["να ", "θα "]:
        if word.startswith(prefix):
            word = word[len(prefix):]
    return word.strip()


def main():
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    cursor = conn.cursor()

    print("=" * 60)
    print("STEP 1: Clean up periphrastic verb forms")
    print("=" * 60)

    # Find periphrastic forms that duplicate base verbs
    periphrastic = [
        ("να έχω", "έχω"),
        ("θα είμαι", "είμαι"),
    ]

    for peri_form, base_form in periphrastic:
        cursor.execute("SELECT id, greek, english FROM words WHERE greek = ?", (peri_form,))
        row = cursor.fetchone()
        if not row:
            print(f"\n  '{peri_form}' not found in database, skipping.")
            continue

        word_id = row[0]
        print(f"\n  Found '{peri_form}' (id={word_id}, english='{row[2]}')")

        # Check for examples
        cursor.execute("SELECT COUNT(*) FROM examples WHERE word_id = ?", (word_id,))
        example_count = cursor.fetchone()[0]
        print(f"    Examples: {example_count}")

        # Check for conjugations
        cursor.execute("SELECT COUNT(*) FROM conjugations WHERE word_id = ?", (word_id,))
        conj_count = cursor.fetchone()[0]
        print(f"    Conjugations: {conj_count}")

        # Delete conjugations (they're duplicates of the base verb)
        if conj_count > 0:
            cursor.execute("DELETE FROM conjugations WHERE word_id = ?", (word_id,))
            print(f"    Deleted {conj_count} duplicate conjugations")

        # Delete examples if any
        if example_count > 0:
            cursor.execute("DELETE FROM examples WHERE word_id = ?", (word_id,))
            print(f"    Deleted {example_count} examples")

        # Delete the word itself
        cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
        print(f"    Deleted word '{peri_form}' (id={word_id})")

    conn.commit()

    print()
    print("=" * 60)
    print("STEP 2: Find verbs with incomplete conjugations")
    print("=" * 60)

    cursor.execute("""
        SELECT w.id, w.greek, COUNT(c.id) as cnt
        FROM words w
        LEFT JOIN conjugations c ON c.word_id = w.id
        WHERE w.part_of_speech = 'verb'
        GROUP BY w.id
        HAVING cnt > 0 AND cnt < 18
    """)
    incomplete_verbs = cursor.fetchall()

    if not incomplete_verbs:
        print("\n  No verbs with incomplete (but non-zero) conjugations found.")
    else:
        print(f"\n  Found {len(incomplete_verbs)} verb(s) with incomplete conjugations:")
        for word_id, greek, cnt in incomplete_verbs:
            print(f"    - {greek} (id={word_id}): {cnt}/18 forms")

    for word_id, greek, cnt in incomplete_verbs:
        print(f"\n  Processing: {greek} (id={word_id}, has {cnt} forms)")

        # Find which tenses are already present
        cursor.execute(
            "SELECT DISTINCT tense FROM conjugations WHERE word_id = ?",
            (word_id,),
        )
        existing_tenses = {row[0] for row in cursor.fetchall()}
        missing_tenses = {"present", "past", "future"} - existing_tenses
        print(f"    Existing tenses: {sorted(existing_tenses)}")
        print(f"    Missing tenses: {sorted(missing_tenses)}")

        if not missing_tenses:
            print("    All tenses present (but some persons may be missing), skipping.")
            continue

        verb = get_verb_stem(greek)
        print(f"    Looking up: {verb}")

        html = fetch_conjugation_page(verb)
        if html is None:
            print(f"    Could not fetch conjugation page, skipping.")
            continue

        all_conjugations = parse_conjugations(html)
        if not all_conjugations:
            print(f"    No conjugations found in HTML, skipping.")
            continue

        inserted = 0
        for tense in sorted(missing_tenses):
            if tense not in all_conjugations:
                print(f"    WARNING: tense '{tense}' not found on Cooljugator page")
                continue

            persons = all_conjugations[tense]
            for person, form in sorted(persons.items()):
                cursor.execute(
                    "INSERT INTO conjugations (word_id, tense, person, conjugation) "
                    "VALUES (?, ?, ?, ?)",
                    (word_id, tense, person, form),
                )
                print(f"    + {tense}/{person}: {form}")
                inserted += 1

        print(f"    Inserted {inserted} new conjugation forms")

    conn.commit()

    # Final verification
    print()
    print("=" * 60)
    print("STEP 3: Verification")
    print("=" * 60)

    cursor.execute("""
        SELECT w.id, w.greek, COUNT(c.id) as cnt
        FROM words w
        LEFT JOIN conjugations c ON c.word_id = w.id
        WHERE w.part_of_speech = 'verb'
        GROUP BY w.id
        HAVING cnt > 0 AND cnt < 18
    """)
    still_incomplete = cursor.fetchall()

    if still_incomplete:
        print(f"\n  WARNING: {len(still_incomplete)} verb(s) still have incomplete conjugations:")
        for word_id, greek, cnt in still_incomplete:
            print(f"    - {greek} (id={word_id}): {cnt}/18 forms")
    else:
        print("\n  All verbs with conjugations now have complete sets (18 forms each).")

    # Show summary of verbs with full conjugations
    cursor.execute("""
        SELECT COUNT(DISTINCT w.id)
        FROM words w
        JOIN conjugations c ON c.word_id = w.id
        WHERE w.part_of_speech = 'verb'
        GROUP BY w.id
        HAVING COUNT(c.id) = 18
    """)
    complete_count = len(cursor.fetchall())
    print(f"  Verbs with complete conjugations: {complete_count}")

    # Check that periphrastic forms are gone
    cursor.execute("SELECT id, greek FROM words WHERE greek IN ('να έχω', 'θα είμαι')")
    leftover = cursor.fetchall()
    if leftover:
        print(f"\n  WARNING: Periphrastic forms still in DB: {leftover}")
    else:
        print("  Periphrastic duplicates ('να έχω', 'θα είμαι') successfully removed.")

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
