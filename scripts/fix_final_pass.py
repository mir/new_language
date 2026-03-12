# /// script
# dependencies = []
# requires-python = ">=3.12"
# ///
"""Final cleanup pass for remaining nouns without articles and more misclassified words."""

import sqlite3

DB_PATH = "db/greek_b1.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    changes = 0

    # === Reclassify verb forms still tagged as noun ===
    verb_forms = [864, 867, 869, 870, 871, 872, 1112, 1233, 1254, 1272, 1274, 1275, 1277, 1426, 1468, 2008]
    for wid in verb_forms:
        cur.execute("UPDATE words SET part_of_speech = 'verb form' WHERE id = ?", (wid,))
        changes += 1
    print(f"Reclassified {len(verb_forms)} verb forms")

    # === Reclassify adjectives ===
    adjectives = {
        626: None, 1088: None, 1097: None, 1100: None, 1495: None,
        # These are substantivized adjectives — they function as nouns in Greek
        # Keep them as nouns: 822 (ουσιαστικό=noun), 1038, 1050, 1121, 1310, 1319, 1329,
        # 1406, 1489, 1498, 1500, 1593, 1906, 1916, 1918, 1919, 1920, 1921, 2095, 2153
    }
    for wid in adjectives:
        cur.execute("UPDATE words SET part_of_speech = 'adjective' WHERE id = ?", (wid,))
        changes += 1
    print(f"Reclassified {len(adjectives)} adjectives")

    # === Reclassify μοβ as adjective ===
    cur.execute("UPDATE words SET part_of_speech = 'adjective' WHERE id = 906")
    changes += 1

    # === Assign articles to feminine nouns ending in -η/-ή ===
    feminine_h = {
        935: "η", 952: "η", 998: "η", 1013: "η", 1025: "η", 1163: "η", 1171: "η",
        1283: "η", 1285: "η", 1297: "η", 1306: "η", 1314: "η", 1535: "η", 1540: "η",
        1545: "η", 1554: "η", 1555: "η", 1556: "η", 1561: "η", 1616: "η", 1704: "η",
        1708: "η", 1758: "η", 1795: "η", 1818: "η", 1923: "η", 2040: "η", 2084: "η",
        2093: "η", 2136: "η", 2156: "η", 2161: "η",
    }
    for wid, art in feminine_h.items():
        row = cur.execute("SELECT greek FROM words WHERE id = ?", (wid,)).fetchone()
        if row:
            cur.execute("UPDATE words SET article = ?, greek = ? WHERE id = ?", (art, f"{art} {row[0]}", wid))
            changes += 1
            print(f"  #{wid} '{row[0]}' → '{art} {row[0]}'")

    # === Assign articles to neuter substantivized adjectives (-ό/-ο) ===
    neuter_o = {
        822: "το", 1038: "το", 1050: "το", 1121: "το", 1310: "το", 1319: "το",
        1329: "το", 1362: "το", 1406: "το", 1489: "το", 1498: "το", 1500: "το",
        1593: "το", 1630: "το", 1906: "το", 1916: "το", 1918: "το", 1919: "το",
        1920: "το", 1921: "το", 2095: "το",
    }
    for wid, art in neuter_o.items():
        row = cur.execute("SELECT greek FROM words WHERE id = ?", (wid,)).fetchone()
        if row:
            cur.execute("UPDATE words SET article = ?, greek = ? WHERE id = ?", (art, f"{art} {row[0]}", wid))
            changes += 1
            print(f"  #{wid} '{row[0]}' → '{art} {row[0]}'")

    # === Neuter nouns ending in -ν (παρελθόν, μέλλον, etc.) ===
    neuter_n = {2029: "το", 2030: "το", 2032: "το", 1627: "το", 1659: "το", 2054: "το"}
    for wid, art in neuter_n.items():
        row = cur.execute("SELECT greek FROM words WHERE id = ?", (wid,)).fetchone()
        if row:
            cur.execute("UPDATE words SET article = ?, greek = ? WHERE id = ?", (art, f"{art} {row[0]}", wid))
            changes += 1
            print(f"  #{wid} '{row[0]}' → '{art} {row[0]}'")

    # === Neuter -υ words ===
    neuter_y = {1740: "το", 2003: "το"}  # δίχτυ, δόρυ
    for wid, art in neuter_y.items():
        row = cur.execute("SELECT greek FROM words WHERE id = ?", (wid,)).fetchone()
        if row:
            cur.execute("UPDATE words SET article = ?, greek = ? WHERE id = ?", (art, f"{art} {row[0]}", wid))
            changes += 1
            print(f"  #{wid} '{row[0]}' → '{art} {row[0]}'")

    # === Masculine month names (ο Ιανουάριος) — but they have slash variants ===
    # Keep as nouns, assign ο article to main form
    months = [940, 941, 942, 943, 944, 948, 949, 950, 951]
    for wid in months:
        row = cur.execute("SELECT greek FROM words WHERE id = ?", (wid,)).fetchone()
        if row:
            cur.execute("UPDATE words SET article = 'ο' WHERE id = ?", (wid,))
            changes += 1
            print(f"  #{wid} '{row[0]}' → article=ο (month name)")

    # === Masculine nouns ===
    masc = {1870: "ο"}  # χαμαιλέων
    for wid, art in masc.items():
        row = cur.execute("SELECT greek FROM words WHERE id = ?", (wid,)).fetchone()
        if row:
            cur.execute("UPDATE words SET article = ?, greek = ? WHERE id = ?", (art, f"{art} {row[0]}", wid))
            changes += 1
            print(f"  #{wid} '{row[0]}' → '{art} {row[0]}'")

    # === Feminine ακτή → already handled above ===

    # === Indeclinable foreign words — assign correct articles ===
    indeclinable = {
        798: ("το", "κασκόλ"),    # scarf - neuter
        803: ("το", "τζιν"),      # jeans - neuter
        808: ("το", "μιτοθφάν"),  # jacket - neuter (loan)
        1128: ("το", "ντους"),    # shower - neuter
        1134: ("το", "χολ"),      # hall - neuter
        1169: ("το", "μπολ"),     # bowl - neuter
        1295: ("το", "μπαρ"),     # bar - neuter
        1508: ("το", "τεστ"),     # test - neuter
        1527: ("το", "προφίλ"),   # profile - neuter
        1541: ("το", "ρεκόρ"),    # record - neuter
        1625: ("το", "χιούμορ"),  # humour - neuter
        1727: ("το", "τένις"),    # tennis - neuter
        1732: ("το", "γκολ"),     # goal - neuter
        1737: ("το", "σουτ"),     # shot - neuter
        1747: ("το", "χάντμπολ"), # handball - neuter
        1752: ("το", "γκολφ"),    # golf - neuter
        2080: ("το", "ρούτερ"),   # router - neuter
        2089: ("το", "φεστιβάλ"), # festival - neuter
        2109: ("το", "τραμ"),     # tram - neuter
        2114: ("το", "τρακτέρ"), # tractor - neuter
        2151: ("το", "ισλάμ"),    # Islam - neuter
    }
    for wid, (art, word) in indeclinable.items():
        cur.execute("UPDATE words SET article = ?, greek = ? WHERE id = ?", (art, f"{art} {word}", wid))
        changes += 1
        print(f"  #{wid} '{word}' → '{art} {word}'")

    # === #826 μετοχή (participle) — grammatical term, feminine ===
    cur.execute("UPDATE words SET article = 'η', greek = 'η μετοχή' WHERE id = 826")
    changes += 1

    # === Plural nouns — keep without article (they use οι/τα in plural) ===
    plural_ids = [988, 1315, 1370, 1487, 1509, 1623, 1892, 1899, 1949, 1970, 2085]
    for wid in plural_ids:
        # These are already fine as plural nouns without singular article
        pass
    print(f"Kept {len(plural_ids)} plural nouns without article (correct for plurals)")

    # === #1454 αμερική → Αμερική (proper noun) ===
    cur.execute("UPDATE words SET greek = 'η Αμερική', article = 'η', part_of_speech = 'proper noun' WHERE id = 1454")
    changes += 1

    # === #1891 κογκρέσου → genitive form, reclassify ===
    cur.execute("UPDATE words SET part_of_speech = 'noun', article = 'το', greek = 'το κογκρέσο', notes = 'κογκρέσου is genitive' WHERE id = 1891")
    changes += 1

    # === #2153 ιερό → neuter adjective/noun ===
    cur.execute("UPDATE words SET article = 'το', greek = 'το ιερό' WHERE id = 2153")
    changes += 1

    # === #1965 φυσική — physics (noun, feminine) ===
    cur.execute("UPDATE words SET article = 'η', greek = 'η φυσική' WHERE id = 1965")
    changes += 1

    conn.commit()
    print(f"\nTotal changes: {changes}")

    # Verification
    no_art = cur.execute("""
        SELECT COUNT(*) FROM words
        WHERE part_of_speech='noun'
          AND (article IS NULL OR article='')
          AND greek NOT LIKE 'ο %'
          AND greek NOT LIKE 'η %'
          AND greek NOT LIKE 'το %'
    """).fetchone()[0]
    print(f"Nouns without articles: {no_art}")

    if no_art > 0:
        remaining = cur.execute("""
            SELECT id, greek, english FROM words
            WHERE part_of_speech='noun'
              AND (article IS NULL OR article='')
              AND greek NOT LIKE 'ο %'
              AND greek NOT LIKE 'η %'
              AND greek NOT LIKE 'το %'
        """).fetchall()
        print("Remaining:")
        for r in remaining:
            print(f"  #{r[0]} '{r[1]}' ({r[2]})")

    # POS distribution
    pos_dist = cur.execute(
        "SELECT part_of_speech, COUNT(*) FROM words GROUP BY part_of_speech ORDER BY COUNT(*) DESC"
    ).fetchall()
    print("\nPOS distribution:")
    for pos, cnt in pos_dist:
        print(f"  {pos}: {cnt}")

    conn.close()


if __name__ == "__main__":
    main()
