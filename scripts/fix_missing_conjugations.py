#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["requests<3", "beautifulsoup4"]
# requires-python = ">=3.12"
# ///

"""Fix missing conjugations for 3 fairy_tale verbs that returned 404 under their base spelling."""

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


def fetch_conjugation_page(verb: str) -> str | None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = urllib.parse.quote(verb, safe="")
    cache_file = CACHE_DIR / f"{safe_name}.html"

    if cache_file.exists():
        content = cache_file.read_text(encoding="utf-8")
        # Reject cached 404 pages
        if "Error 404" in content or "Not Found" in content:
            cache_file.unlink()
        else:
            print(f"    (cached)", end=" ")
            return content

    url = BASE_URL + urllib.parse.quote(verb)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            if "Error 404" in resp.text:
                print(f"    Soft-404 for {verb}", end=" ")
                return None
            cache_file.write_text(resp.text, encoding="utf-8")
            return resp.text
        elif resp.status_code == 404:
            print(f"    Hard-404 for {verb}", end=" ")
            return None
        else:
            print(f"    HTTP {resp.status_code} for {verb}", end=" ")
            return None
    except requests.RequestException as e:
        print(f"    Request error for {verb}: {e}", end=" ")
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


def insert_conjugations(cursor, word_id: int, conjugations: dict) -> int:
    total = 0
    for tense, persons in conjugations.items():
        for person, form in persons.items():
            cursor.execute(
                "INSERT INTO conjugations (word_id, tense, person, conjugation) VALUES (?, ?, ?, ?)",
                (word_id, tense, person, form),
            )
            total += 1
    return total


def try_fetch_and_insert(conn, cursor, word_id: int, candidates: list[str]) -> bool:
    """Try each candidate spelling in order; insert on first success. Returns True if successful."""
    for i, verb in enumerate(candidates):
        if i > 0:
            time.sleep(1.5)
        print(f"    Trying '{verb}'...", end=" ", flush=True)
        html = fetch_conjugation_page(verb)
        if html is None:
            print("FAILED")
            continue
        conjugations = parse_conjugations(html)
        if not conjugations:
            print("no forms found")
            continue
        total = insert_conjugations(cursor, word_id, conjugations)
        conn.commit()
        print(f"OK ({total} forms)")
        return True
    return False


def copy_conjugations(conn, cursor, source_word_id: int, target_word_id: int) -> int:
    """Copy conjugation rows from one word_id to another."""
    cursor.execute(
        "SELECT tense, person, conjugation FROM conjugations WHERE word_id = ?",
        (source_word_id,),
    )
    rows = cursor.fetchall()
    for tense, person, conjugation in rows:
        cursor.execute(
            "INSERT INTO conjugations (word_id, tense, person, conjugation) VALUES (?, ?, ?, ?)",
            (target_word_id, tense, person, conjugation),
        )
    conn.commit()
    return len(rows)


def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # --- χτυπάω (id=2213): try χτυπώ as alternate ---
    cursor.execute("SELECT id FROM words WHERE greek = 'χτυπάω'")
    row = cursor.fetchone()
    if row:
        word_id = row[0]
        cursor.execute("SELECT COUNT(*) FROM conjugations WHERE word_id = ?", (word_id,))
        count = cursor.fetchone()[0]
        if count == 0:
            print(f"χτυπάω (id={word_id}): no conjugations yet, trying alternates...")
            ok = try_fetch_and_insert(conn, cursor, word_id, ["χτυπώ", "χτυπάω"])
            if not ok:
                print(f"  χτυπάω: all alternates failed")
        else:
            print(f"χτυπάω (id={word_id}): already has {count} conjugations — skipping")
    else:
        print("χτυπάω: not found in DB")

    time.sleep(1.5)

    # --- γλιτώνω (id=2215): try γλυτώνω as alternate ---
    cursor.execute("SELECT id FROM words WHERE greek = 'γλιτώνω'")
    row = cursor.fetchone()
    if row:
        word_id = row[0]
        cursor.execute("SELECT COUNT(*) FROM conjugations WHERE word_id = ?", (word_id,))
        count = cursor.fetchone()[0]
        if count == 0:
            print(f"γλιτώνω (id={word_id}): no conjugations yet, trying alternates...")
            ok = try_fetch_and_insert(conn, cursor, word_id, ["γλυτώνω", "γλιτώνω"])
            if not ok:
                print(f"  γλιτώνω: all alternates failed")
        else:
            print(f"γλιτώνω (id={word_id}): already has {count} conjugations — skipping")
    else:
        print("γλιτώνω: not found in DB")

    # --- ξεκινάω (id=2216): copy conjugations from ξεκινώ (id=1190) ---
    cursor.execute("SELECT id FROM words WHERE greek = 'ξεκινάω'")
    row = cursor.fetchone()
    if row:
        xekinao_id = row[0]
        cursor.execute("SELECT COUNT(*) FROM conjugations WHERE word_id = ?", (xekinao_id,))
        count = cursor.fetchone()[0]
        if count == 0:
            # Copy from ξεκινώ
            copied = copy_conjugations(conn, cursor, 1190, xekinao_id)
            print(f"ξεκινάω (id={xekinao_id}): copied {copied} conjugation forms from ξεκινώ (id=1190)")
        else:
            print(f"ξεκινάω (id={xekinao_id}): already has {count} conjugations — skipping")
    else:
        print("ξεκινάω: not found in DB")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
