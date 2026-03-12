# /// script
# dependencies = []
# requires-python = ">=3.12"
# ///
"""
Comprehensive database cleanup script:
1. Merge exact duplicate words (same greek text)
2. Merge near-duplicate noun pairs (bare word + article version)
3. Reclassify misclassified "nouns" (να/θα forms, pronouns, adverbs, etc.)
4. Assign articles to genuine nouns missing them
"""

import sqlite3
import re

DB_PATH = "db/greek_b1.db"


def merge_exact_duplicates(cur):
    """Merge words with identical greek text. Keep the one with more info (category, lower id)."""
    print("\n=== MERGING EXACT DUPLICATES ===")
    dupes = cur.execute("""
        SELECT greek, GROUP_CONCAT(id) as ids
        FROM words GROUP BY greek HAVING COUNT(*) > 1
    """).fetchall()

    merged = 0
    for greek, ids_str in dupes:
        ids = [int(x) for x in ids_str.split(",")]
        # Fetch all rows
        rows = cur.execute(
            f"SELECT id, greek, english, part_of_speech, article, category, notes FROM words WHERE id IN ({','.join('?' * len(ids))})",
            ids,
        ).fetchall()

        # Pick the best one: prefer one with category, then lower id
        best = sorted(rows, key=lambda r: (not bool(r[5]), r[0]))[0]
        keep_id = best[0]
        delete_ids = [r[0] for r in rows if r[0] != keep_id]

        for del_id in delete_ids:
            # Reassign FKs
            cur.execute("UPDATE conjugations SET word_id = ? WHERE word_id = ?", (keep_id, del_id))
            cur.execute("UPDATE examples SET word_id = ? WHERE word_id = ?", (keep_id, del_id))
            cur.execute("DELETE FROM words WHERE id = ?", (del_id,))
            merged += 1
            print(f"  Merged #{del_id} into #{keep_id}: {greek}")

    print(f"Total merged: {merged}")


def merge_near_duplicates(cur):
    """Merge pairs like 'δελφίνι' and 'το δελφίνι' — keep the article version."""
    print("\n=== MERGING NEAR-DUPLICATE PAIRS ===")
    pairs = cur.execute("""
        SELECT w1.id, w1.greek, w2.id, w2.greek
        FROM words w1 JOIN words w2
        ON (w2.greek = 'ο ' || w1.greek OR w2.greek = 'η ' || w1.greek OR w2.greek = 'το ' || w1.greek)
        WHERE w1.part_of_speech = 'noun'
    """).fetchall()

    for bare_id, bare_greek, art_id, art_greek in pairs:
        cur.execute("UPDATE conjugations SET word_id = ? WHERE word_id = ?", (art_id, bare_id))
        cur.execute("UPDATE examples SET word_id = ? WHERE word_id = ?", (art_id, bare_id))
        cur.execute("DELETE FROM words WHERE id = ?", (bare_id,))
        print(f"  Merged #{bare_id} '{bare_greek}' into #{art_id} '{art_greek}'")

    print(f"Total near-duplicates merged: {len(pairs)}")


def reclassify_nouns(cur):
    """Reclassify words incorrectly tagged as noun."""
    print("\n=== RECLASSIFYING MISCLASSIFIED NOUNS ===")

    # Get all nouns
    nouns = cur.execute(
        "SELECT id, greek, english FROM words WHERE part_of_speech = 'noun'"
    ).fetchall()

    # να / θα forms → verb form
    na_tha = [(id, greek) for id, greek, _ in nouns if greek.startswith("να ") or greek.startswith("θα ")]

    pronouns = {
        "εγώ", "εσύ", "αυτός", "αυτή", "αυτό", "εμείς", "εσείς", "αυτοί", "αυτές", "αυτά",
        "μου", "σου", "του", "της", "μας", "σας", "τους",
        "κάτι", "κάποιος", "κάποια", "κάποιο", "τίποτα", "τίποτε", "κανείς", "κανένας", "καμία",
        "ποιος", "ποια", "ποιο", "πόσος", "πόση", "πόσο",
        "όλος", "όλη", "όλο", "κάθε", "άλλος", "άλλη", "άλλο",
        "ίδιος", "ίδια", "ίδιο", "μόνος", "μόνη", "μόνο",
    }

    adverbs = {
        "πολύ", "λίγο", "αρκετά", "ήδη", "ακόμα", "ακόμη", "πάντα", "ποτέ",
        "σήμερα", "αύριο", "χθες", "τώρα", "εδώ", "εκεί",
        "πάνω", "κάτω", "μέσα", "έξω", "μπροστά", "πίσω",
        "δεξιά", "αριστερά", "γρήγορα", "αργά", "καλά", "σωστά",
        "πιο", "πώς", "πού", "πότε", "γιατί", "μαζί", "μόνο",
        "συνήθως", "αμέσως", "ξανά", "σχεδόν", "μόλις", "ξαφνικά",
        "δυνατά", "σιγά", "κοντά", "μακριά", "νωρίς", "αργά",
        "περίπου", "τελικά", "ειδικά", "ιδιαίτερα", "επίσης",
    }

    conjunctions = {
        "και", "ή", "αλλά", "όμως", "ωστόσο", "γιατί", "επειδή",
        "αν", "όταν", "ενώ", "αφού", "μόλις", "πριν", "ώσπου",
        "ούτε", "είτε", "μήτε", "ότι", "πως", "μήπως",
    }

    prepositions = {
        "σε", "από", "με", "για", "προς", "χωρίς", "μετά", "πριν",
        "κατά", "μέχρι", "ανάμεσα", "μεταξύ", "εναντίον", "παρά",
        "εκτός", "εντός", "κοντά σε", "μακριά από",
    }

    particles = {
        "ναι", "όχι", "ίσως", "βέβαια", "φυσικά", "μάλιστα",
        "δεν", "μη", "μην", "θα", "να", "ας",
    }

    reclassified = 0

    for wid, greek, english in nouns:
        new_pos = None

        # να/θα forms
        if greek.startswith("να ") or greek.startswith("θα "):
            new_pos = "verb form"
        elif greek in pronouns:
            new_pos = "pronoun"
        elif greek in adverbs:
            new_pos = "adverb"
        elif greek in conjunctions:
            new_pos = "conjunction"
        elif greek in prepositions:
            new_pos = "preposition"
        elif greek in particles:
            new_pos = "particle"
        # Multi-word without article — likely a phrase
        elif " " in greek and not re.match(r"^(ο|η|το) ", greek):
            new_pos = "phrase"
        # Verb-like endings
        elif re.search(r"(ώ|ω)$", greek) and not re.match(r"^(ο|η|το) ", greek):
            # Check if it looks like a verb (ends in -ω/-ώ and has no article)
            # Be careful: some nouns end in -ω too (rare)
            # Only reclassify if english suggests it's a verb (starts with "to ")
            if english and english.lower().startswith("to "):
                new_pos = "verb"

        if new_pos:
            cur.execute("UPDATE words SET part_of_speech = ? WHERE id = ?", (new_pos, wid))
            reclassified += 1
            print(f"  #{wid} '{greek}' ({english}): noun → {new_pos}")

    print(f"Total reclassified: {reclassified}")


def assign_articles(cur):
    """Assign articles to genuine nouns that are missing them."""
    print("\n=== ASSIGNING ARTICLES TO NOUNS ===")

    # Common neuter nouns ending in -ος (exceptions to masculine rule)
    neuter_os = {
        "δάσος", "λάθος", "μέρος", "πάθος", "κράτος", "βάρος", "μέγεθος",
        "έδαφος", "στέλεχος", "γεγονός", "καθεστώς", "πλήθος", "είδος",
        "μήκος", "βάθος", "ύψος", "πλάτος", "πάχος", "κέρδος", "έθνος",
        "σθένος", "ήθος", "πένθος", "τέλος", "μίσος",
    }

    nouns = cur.execute("""
        SELECT id, greek, article FROM words
        WHERE part_of_speech = 'noun'
          AND (article IS NULL OR article = '')
          AND greek NOT LIKE 'ο %'
          AND greek NOT LIKE 'η %'
          AND greek NOT LIKE 'το %'
    """).fetchall()

    assigned = 0
    ambiguous = []

    for wid, greek, article in nouns:
        word = greek.strip()
        art = None

        # Neuter exceptions first
        if word in neuter_os:
            art = "το"
        # Neuter endings
        elif word.endswith("μα"):
            art = "το"
        elif word.endswith("ιμο") or word.endswith("σιμο"):
            art = "το"
        elif word.endswith("ί"):
            art = "το"
        elif word.endswith("ι") and not word.endswith("οι"):
            art = "το"
        elif word.endswith("ο") and not word.endswith("ω"):
            art = "το"
        # Masculine endings
        elif word.endswith("ός") or word.endswith("ος"):
            art = "ο"
        elif word.endswith("ής") or word.endswith("ης"):
            art = "ο"
        elif word.endswith("άς") or word.endswith("ας"):
            art = "ο"
        elif word.endswith("έας"):
            art = "ο"
        elif word.endswith("ές"):
            art = "ο"
        elif word.endswith("ούς"):
            art = "ο"
        # Feminine endings
        elif word.endswith("η"):
            art = "η"
        elif word.endswith("α"):
            art = "η"
        elif word.endswith("ση"):
            art = "η"
        elif word.endswith("ξη"):
            art = "η"
        elif word.endswith("ψη"):
            art = "η"
        elif word.endswith("ία"):
            art = "η"
        elif word.endswith("εια"):
            art = "η"
        elif word.endswith("ού"):
            art = "η"

        if art:
            new_greek = f"{art} {word}"
            cur.execute(
                "UPDATE words SET article = ?, greek = ? WHERE id = ?",
                (art, new_greek, wid),
            )
            assigned += 1
            print(f"  #{wid} '{word}' → '{new_greek}'")
        else:
            ambiguous.append((wid, word))

    print(f"Total assigned: {assigned}")
    if ambiguous:
        print(f"\nAmbiguous ({len(ambiguous)} words, left unchanged):")
        for wid, word in ambiguous:
            print(f"  #{wid} '{word}'")


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        # Step 1: Merge exact duplicates
        merge_exact_duplicates(cur)

        # Step 2: Merge near-duplicate pairs
        merge_near_duplicates(cur)

        # Step 3: Reclassify misclassified nouns
        reclassify_nouns(cur)

        # Step 4: Assign articles to remaining nouns
        assign_articles(cur)

        conn.commit()
        print("\n=== ALL CHANGES COMMITTED ===")

        # Verification
        print("\n=== VERIFICATION ===")

        exact_dupes = cur.execute(
            "SELECT COUNT(*) FROM (SELECT greek FROM words GROUP BY greek HAVING COUNT(*) > 1)"
        ).fetchone()[0]
        print(f"Exact duplicates remaining: {exact_dupes}")

        near_dupes = cur.execute("""
            SELECT COUNT(*) FROM words w1 JOIN words w2
            ON (w2.greek = 'ο '||w1.greek OR w2.greek = 'η '||w1.greek OR w2.greek = 'το '||w1.greek)
            WHERE w1.part_of_speech='noun'
        """).fetchone()[0]
        print(f"Near-duplicate pairs remaining: {near_dupes}")

        nouns_no_article = cur.execute("""
            SELECT COUNT(*) FROM words
            WHERE part_of_speech='noun'
              AND (article IS NULL OR article='')
              AND greek NOT LIKE 'ο %'
              AND greek NOT LIKE 'η %'
              AND greek NOT LIKE 'το %'
        """).fetchone()[0]
        print(f"Nouns without articles: {nouns_no_article}")

        incomplete_verbs = cur.execute("""
            SELECT w.greek, COUNT(c.id) FROM words w
            JOIN conjugations c ON c.word_id = w.id
            WHERE w.part_of_speech = 'verb'
            GROUP BY w.id HAVING COUNT(c.id) < 18
        """).fetchall()
        print(f"Verbs with incomplete conjugations: {len(incomplete_verbs)}")
        if incomplete_verbs:
            for greek, cnt in incomplete_verbs:
                print(f"  {greek}: {cnt} forms")

        total = cur.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        print(f"\nTotal words in database: {total}")

        # POS distribution
        pos_dist = cur.execute(
            "SELECT part_of_speech, COUNT(*) FROM words GROUP BY part_of_speech ORDER BY COUNT(*) DESC"
        ).fetchall()
        print("\nPart of speech distribution:")
        for pos, cnt in pos_dist:
            print(f"  {pos}: {cnt}")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
