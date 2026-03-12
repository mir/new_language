# /// script
# dependencies = []
# requires-python = ">=3.12"
# ///
"""
Fix words that were incorrectly assigned articles:
1. Verb forms tagged as nouns (3rd person forms like τρέχει, πληρώνει etc.)
2. Adjectives tagged as nouns (ending in -ός/-ή/-ό/-ικός etc.)
3. Other misclassified words (letters, imperative forms, past tense forms, etc.)
"""

import sqlite3
import re

DB_PATH = "db/greek_b1.db"


def fix_misassigned(cur):
    print("=== FIXING MISASSIGNED WORDS ===")

    # Get all nouns that were assigned articles by the previous script
    # These are suspect — check if they're really nouns
    nouns = cur.execute("""
        SELECT id, greek, english, article, part_of_speech FROM words
        WHERE part_of_speech = 'noun'
    """).fetchall()

    fixes = []

    for wid, greek, english, article, pos in nouns:
        # Strip article prefix to get bare word
        bare = greek
        for art in ("ο ", "η ", "το "):
            if greek.startswith(art):
                bare = greek[len(art):]
                break

        new_pos = None
        remove_article = False

        # Greek alphabet letters (single uppercase letters)
        if re.match(r'^[Α-Ω]$', bare):
            new_pos = "letter"
            remove_article = True

        # Verb forms - 3rd person singular/plural present (ends in -ει, -ουν, -ονται, -εται, -ούνται)
        elif re.search(r'(ει|ούν|ουν|εται|ονται|ούνται|ίζονται|ίζεται|ηθεί)$', bare) and not bare.endswith("κλειδί"):
            # Check english to confirm - should be "he/she/it ..." or just a verb
            if english and not any(bare == w for w in ["μαχαίρι", "κομμάτι", "ψαλίδι", "τηγάνι"]):
                # These are clearly verb forms, not nouns
                verb_patterns = [
                    "ει$",  # 3rd person singular: τρέχει, πληρώνει, etc
                ]
                if re.search(r'(ει|ούν|ουν|εται|ονται|ούνται)$', bare):
                    # Verify by english: if english doesn't look like a noun concept
                    eng_lower = english.lower()
                    if any(eng_lower.startswith(p) for p in ["he ", "she ", "it ", "they ", "(he)", "(she)", "(it)", "(they)"]):
                        new_pos = "verb form"
                        remove_article = True
                    elif eng_lower in ["believes", "gives", "writes", "hears", "costs", "means", "says",
                                       "is forbidden", "is paid", "is located", "are designed",
                                       "gets wet", "dream", "is heard", "is cooked", "is drunk",
                                       "is worn", "is read", "is used", "sits", "are spoken",
                                       "is written", "is eaten", "they sign", "they remember",
                                       "they work", "they return", "they can", "we refer",
                                       "they check", "went up"]:
                        new_pos = "verb form"
                        remove_article = True

        # Past tense verb forms
        elif re.search(r'(ησε|ηκε|ψες|ψε|ξε|αμε|ατε|αν|ες)$', bare):
            eng_lower = (english or "").lower()
            if eng_lower and any(eng_lower.startswith(p) for p in ["(i) ", "(he)", "(she)", "(it)", "(we)", "(you)", "(they)"]):
                new_pos = "verb form"
                remove_article = True
            elif bare in ["μαγείρεψες", "είπε", "έγραψε", "ήπιαμε", "είδες", "σταμάτησε",
                          "έμεινε", "αγάπησε", "ήξερε", "τραυμάτισε", "ανέβηκε"]:
                new_pos = "verb form"
                remove_article = True

        # Imperative verb forms
        elif bare in ["βλέπε", "φέρε", "μάθε", "πείτε", "φάε", "άκουσε", "κλείσε",
                       "περπατήστε", "απάντησε", "τρέχε", "χρησιμοποίησε", "βρες",
                       "γράφε", "μαγείρεψε", "βάλε", "πάρτε", "δώσε"]:
            new_pos = "verb form"
            remove_article = True

        # Subjunctive aorist forms (3rd person)
        elif bare in ["ακούσει", "δώσει"]:
            new_pos = "verb form"
            remove_article = True

        # Adjectives - words ending in -ός/-ικός/-ινός that are clearly adjectives
        adj_words = {
            "ανοιχτός", "μελλοντικός", "πιθανός", "πραγματικός", "βασικός",
            "διαφορετικός", "τελικός", "προσωπικός", "αριστερός", "στρατιωτικός",
            "καθαρός", "ζωντανός", "ζωολογικός", "τριπλός", "διπλός",
            "εθνικός", "μοχθηρός", "οικονομικός", "νεκρός", "μπροστινός",
            "διπλανός",
        }
        if bare in adj_words:
            new_pos = "adjective"
            remove_article = True

        # Adjective forms (feminine/neuter endings)
        adj_fem_neut = {
            "φυσιολογική", "ιστορική", "γενική", "πολιτιστική", "αποδοτική",
            "ευρωπαϊκή", "νομισματική", "επιστημονική", "γαλλική",
            "διαλεκτική", "γεωμετρικό", "τριγωνικό", "χριστιανικό",
            "παραδοσιακό", "αρνητικό", "σοβαρό", "βολικό", "αργό",
            "συχνό", "φτηνό", "ψηλό", "κοντό", "αρκετό", "πολλή",
            "τεχνική", "ηθική", "λογική",
        }
        if bare in adj_fem_neut:
            new_pos = "adjective"
            remove_article = True

        # Words that are really adverbs
        adverb_words = {"επιτέλους", "τότε", "πιθανώς", "τελείως", "οπουδήποτε",
                        "τουλάχιστον", "απλώς", "ακριβώς", "απόψε", "πέρυσι",
                        "απέναντι", "όπου"}
        if bare in adverb_words:
            new_pos = "adverb"
            remove_article = True

        # Interjections / special words
        special = {"Όχι": "interjection", "Ναι": "interjection", "μηδέν": "numeral",
                   "δεκαπέντε": "numeral", "δεκαέξι": "numeral", "Καλοκαίρι": "noun",
                   "ήταν": "verb form", "έτσι": "adverb"}
        if bare in special:
            new_pos = special[bare]
            if new_pos != "noun":
                remove_article = True
            else:
                remove_article = False

        # Plural forms - these should stay as nouns but note they're plural
        plural_words = {"γονείς", "άνθρωποι", "χιλιάδες", "τόνοι", "νόμοι",
                        "αμφιβολίες", "γνώσεις", "επενδύσεις", "μοίρες",
                        "λεπτομέρειες", "κοινοποιήσεις"}
        if bare in plural_words:
            new_pos = "noun"  # keep as noun
            remove_article = True  # but remove wrongly assigned article

        # Pronouns / relative
        if bare in {"αυτός/αυτή/αυτό", "που", "ό,τι", "ποιός"}:
            new_pos = "pronoun"
            remove_article = True

        # Conjunction
        if bare in {"ούτε...ούτε", "είτε...είτε", "σαν"}:
            new_pos = "conjunction"
            remove_article = True

        # Words with slashes (month variants etc) - should be nouns without article prefix wrongly applied
        if "/" in bare and bare not in {"αυτός/αυτή/αυτό"}:
            # These are alternate forms, keep as noun but remove article from greek
            remove_article = True
            new_pos = "noun"

        # Indeclinable foreign words that shouldn't get articles assigned by heuristic
        indeclinable = {"κασκόλ", "τζιν", "μιτοθφάν", "μοβ", "μπαρ", "τεστ", "προφίλ",
                        "ρεκόρ", "χιούμορ", "γκολ", "σουτ", "χάντμπολ", "γκολφ", "τένις",
                        "τραμ", "τρακτέρ", "ρούτερ", "φεστιβάλ", "ισλάμ", "χολ", "ντους",
                        "μπολ"}
        if bare in indeclinable:
            # These need manual article assignment - remove auto-assigned one
            remove_article = True
            # keep as noun

        if new_pos and new_pos != pos:
            if remove_article and article:
                cur.execute("UPDATE words SET part_of_speech = ?, greek = ?, article = NULL WHERE id = ?",
                           (new_pos, bare, wid))
                print(f"  #{wid} '{greek}' → '{bare}' (noun → {new_pos}, removed article)")
            else:
                cur.execute("UPDATE words SET part_of_speech = ? WHERE id = ?", (new_pos, wid))
                print(f"  #{wid} '{greek}': noun → {new_pos}")
            fixes.append(wid)
        elif remove_article and not new_pos:
            # Just remove the wrongly assigned article, keep as noun
            if article and greek.startswith(("ο ", "η ", "το ")):
                cur.execute("UPDATE words SET greek = ?, article = NULL WHERE id = ?", (bare, wid))
                print(f"  #{wid} '{greek}' → '{bare}' (removed wrong article)")
                fixes.append(wid)

    print(f"\nTotal fixes: {len(fixes)}")


def fix_passive_verb_forms(cur):
    """Fix words that are passive/middle voice verb forms incorrectly tagged as nouns."""
    print("\n=== FIXING PASSIVE VERB FORMS ===")

    # Find nouns that look like passive verbs
    rows = cur.execute("""
        SELECT id, greek, english FROM words
        WHERE part_of_speech = 'noun'
        AND (greek LIKE 'το %εται' OR greek LIKE 'το %ονται' OR greek LIKE 'το %ούνται'
             OR greek LIKE 'το %ούν' OR greek LIKE 'το %ουν' OR greek LIKE 'το %ει')
    """).fetchall()

    for wid, greek, english in rows:
        bare = greek
        for art in ("ο ", "η ", "το "):
            if greek.startswith(art):
                bare = greek[len(art):]
                break

        # Check if this is really a verb form
        if re.search(r'(εται|ονται|ούνται|ούν|ουν|ει|αστε)$', bare):
            # Check english to make sure
            eng = (english or "").lower()
            verb_indicators = ["is ", "are ", "can ", "was ", "were ", "they ", "he ", "she ",
                              "it ", "we ", "you ", "believe", "give", "write", "hear",
                              "cost", "mean", "say", "sign", "remember", "work", "return",
                              "check", "refer"]
            if any(eng.startswith(v) or eng == v for v in verb_indicators):
                cur.execute("UPDATE words SET part_of_speech = 'verb form', greek = ?, article = NULL WHERE id = ?",
                           (bare, wid))
                print(f"  #{wid} '{greek}' → '{bare}' (noun → verb form)")


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        fix_misassigned(cur)
        fix_passive_verb_forms(cur)
        conn.commit()
        print("\n=== CHANGES COMMITTED ===")

        # Quick stats
        total = cur.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        pos_dist = cur.execute(
            "SELECT part_of_speech, COUNT(*) FROM words GROUP BY part_of_speech ORDER BY COUNT(*) DESC"
        ).fetchall()
        print(f"\nTotal words: {total}")
        print("POS distribution:")
        for pos, cnt in pos_dist:
            print(f"  {pos}: {cnt}")

        # Remaining nouns without articles
        no_art = cur.execute("""
            SELECT COUNT(*) FROM words
            WHERE part_of_speech='noun'
              AND (article IS NULL OR article='')
              AND greek NOT LIKE 'ο %'
              AND greek NOT LIKE 'η %'
              AND greek NOT LIKE 'το %'
        """).fetchone()[0]
        print(f"\nNouns still without articles: {no_art}")

    except Exception as e:
        conn.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
