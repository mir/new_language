#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["requests<3", "beautifulsoup4"]
# requires-python = ">=3.12"
# ///

"""Scrapes verb conjugations from cooljugator.com and inserts into the database."""

import sqlite3
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DB_PATH = Path(__file__).parent.parent / "db" / "greek_b1.db"
CACHE_DIR = Path(__file__).parent.parent / "db" / "conjugation_cache"
BASE_URL = "https://cooljugator.com/gr/"

# Cooljugator cell ID prefixes mapped to our tense names and person codes.
# IDs follow the pattern: <tense_prefix><number> where numbers 1-6 map to persons.
# Special case: present tense uses "infinitive0" for 1s and "present2-6" for the rest.
TENSE_ID_MAP = {
    "present": {
        "infinitive0": "1s",
        "present2": "2s",
        "present3": "3s",
        "present4": "1p",
        "present5": "2p",
        "present6": "3p",
    },
    "future": {f"future{i}": p for i, p in [(1, "1s"), (2, "2s"), (3, "3s"), (4, "1p"), (5, "2p"), (6, "3p")]},
    "past": {f"pastperfect{i}": p for i, p in [(1, "1s"), (2, "2s"), (3, "3s"), (4, "1p"), (5, "2p"), (6, "3p")]},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def get_verb_stem(greek: str) -> str:
    """Extract the verb from the greek text (remove articles, particles, etc.)."""
    # Remove common prefixes like "να ", "θα "
    word = greek.strip()
    for prefix in ["να ", "θα "]:
        if word.startswith(prefix):
            word = word[len(prefix):]
    return word.strip()


def fetch_conjugation_page(verb: str) -> str | None:
    """Fetch the conjugation page, using cache if available."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Create a safe filename from the verb
    safe_name = urllib.parse.quote(verb, safe="")
    cache_file = CACHE_DIR / f"{safe_name}.html"

    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8")

    url = BASE_URL + urllib.parse.quote(verb)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            cache_file.write_text(resp.text, encoding="utf-8")
            return resp.text
        elif resp.status_code == 404:
            print(f"    Not found on cooljugator: {verb}")
            return None
        else:
            print(f"    HTTP {resp.status_code} for {verb}")
            return None
    except requests.RequestException as e:
        print(f"    Request error for {verb}: {e}")
        return None


def parse_conjugations(html: str) -> dict[str, dict[str, str]]:
    """Parse conjugation tables from cooljugator HTML.

    Cooljugator puts each conjugation form in a div with a unique id
    (e.g. "infinitive0", "present2", "future1", "pastperfect3") and the
    actual form text in a ``data-default`` attribute.
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

    return results


def scrape_conjugations():
    """Main function to scrape conjugations for all verbs in the database."""
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all verbs
    cursor.execute("SELECT id, greek FROM words WHERE part_of_speech = 'verb'")
    verbs = cursor.fetchall()
    print(f"Found {len(verbs)} verbs in database", flush=True)

    # Check which already have conjugations
    cursor.execute("SELECT DISTINCT word_id FROM conjugations")
    already_done = {row[0] for row in cursor.fetchall()}
    verbs_to_process = [(wid, greek) for wid, greek in verbs if wid not in already_done]
    print(f"  {len(already_done)} already have conjugations, {len(verbs_to_process)} to process", flush=True)

    success_count = 0
    fail_count = 0

    for i, (word_id, greek) in enumerate(verbs_to_process):
        verb = get_verb_stem(greek)
        print(f"  [{i + 1}/{len(verbs_to_process)}] {verb}...", end=" ", flush=True)

        html = fetch_conjugation_page(verb)
        if html is None:
            fail_count += 1
            print("SKIP", flush=True)
            continue

        conjugations = parse_conjugations(html)
        if not conjugations:
            print("no conjugations found", flush=True)
            fail_count += 1
            continue

        total_forms = 0
        for tense, persons in conjugations.items():
            for person, form in persons.items():
                cursor.execute(
                    "INSERT INTO conjugations (word_id, tense, person, conjugation) VALUES (?, ?, ?, ?)",
                    (word_id, tense, person, form)
                )
                total_forms += 1

        print(f"OK ({total_forms} forms)", flush=True)
        success_count += 1

        # Commit every 20 verbs to avoid losing progress
        if success_count % 20 == 0:
            conn.commit()

        # Rate limiting - be respectful
        if i < len(verbs_to_process) - 1:
            time.sleep(1.5)

    conn.commit()
    conn.close()

    print(f"\nDone! Successfully scraped: {success_count}, Failed: {fail_count}", flush=True)


if __name__ == "__main__":
    scrape_conjugations()
