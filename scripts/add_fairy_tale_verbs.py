#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["requests<3", "beautifulsoup4"]
# requires-python = ">=3.12"
# ///

"""Add missing fairy_tale verbs to the Greek B1 database and scrape their conjugations."""

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
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

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

# Verbs confirmed NOT in the database, to be added under category 'fairy_tales'
NEW_VERBS = [
    ("προσέχω", "to be careful / pay attention"),
    ("αφήνω", "to leave / let / allow"),
    ("κελαηδώ", "to chirp / warble"),
    ("μαζεύω", "to pick / collect / gather"),
    ("παραμονεύω", "to lurk / lie in wait"),
    ("χτυπάω", "to hit / beat / knock"),
    ("σκίζω", "to rip / tear / cut open"),
    ("γλιτώνω", "to escape / be saved / survive"),
    # ξεκινάω: ξεκινώ already exists (id 1190), but ξεκινάω variant is absent — add it
    ("ξεκινάω", "to start / begin"),
]


def fetch_conjugation_page(verb: str) -> str | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = urllib.parse.quote(verb, safe="")
    cache_file = CACHE_DIR / f"{safe_name}.html"

    if cache_file.exists():
        print(f"    (cached)", end=" ")
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


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    skipped = []
    added = []
    conjugation_results = []

    for greek, english in NEW_VERBS:
        # Double-check: skip if already present
        cursor.execute("SELECT id FROM words WHERE greek = ?", (greek,))
        row = cursor.fetchone()
        if row:
            skipped.append((greek, row[0], "already in db"))
            print(f"SKIP  {greek} — already exists (id={row[0]})")
            continue

        # Insert the word
        cursor.execute(
            "INSERT INTO words (greek, english, part_of_speech, article, category, notes) VALUES (?, ?, 'verb', NULL, 'fairy_tales', NULL)",
            (greek, english),
        )
        word_id = cursor.lastrowid
        conn.commit()
        added.append((greek, word_id, english))
        print(f"ADD   {greek} (id={word_id}) — {english}")

        # Scrape conjugations
        print(f"      Fetching conjugations for {greek}...", end=" ", flush=True)
        html = fetch_conjugation_page(greek)
        if html is None:
            conjugation_results.append((greek, word_id, 0, "fetch failed"))
            print("FAILED")
            continue

        conjugations = parse_conjugations(html)
        if not conjugations:
            conjugation_results.append((greek, word_id, 0, "no conjugations found"))
            print("no conjugations found")
            continue

        total_forms = 0
        for tense, persons in conjugations.items():
            for person, form in persons.items():
                cursor.execute(
                    "INSERT INTO conjugations (word_id, tense, person, conjugation) VALUES (?, ?, ?, ?)",
                    (word_id, tense, person, form),
                )
                total_forms += 1

        conn.commit()
        conjugation_results.append((greek, word_id, total_forms, "OK"))
        print(f"OK ({total_forms} forms)")

        time.sleep(1.5)

    conn.close()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    print(f"\nSkipped ({len(skipped)} verbs — already in database):")
    for greek, wid, reason in skipped:
        print(f"  {greek} (id={wid})")

    print(f"\nAdded ({len(added)} new verbs):")
    for greek, wid, english in added:
        print(f"  {greek} (id={wid}) — {english}")

    print(f"\nConjugation results:")
    for greek, wid, forms, status in conjugation_results:
        print(f"  {greek}: {status}" + (f", {forms} forms" if forms else ""))


if __name__ == "__main__":
    main()
