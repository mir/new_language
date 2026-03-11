#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["pyyaml"]
# requires-python = ">=3.12"
# ///

import sqlite3
import yaml
from collections import defaultdict
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "greek_b1.db"
OUT_PATH = Path(__file__).parent.parent / "db" / "greek_b1.yml"


class FlowMap(dict):
    """Dict that YAML dumps in flow style."""
    pass


def flow_map_representer(dumper, data):
    return dumper.represent_mapping("tag:yaml.org,2002:map", data, flow_style=True)


yaml.add_representer(FlowMap, flow_map_representer)


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Load conjugations grouped by word_id -> tense -> {person: form}
    conj_map = defaultdict(lambda: defaultdict(dict))
    for row in conn.execute("SELECT word_id, tense, person, conjugation FROM conjugations ORDER BY word_id, tense, person"):
        conj_map[row["word_id"]][row["tense"]][row["person"]] = row["conjugation"]

    # Load words
    entries = []
    for row in conn.execute("SELECT id, greek, english, part_of_speech, article, category FROM words ORDER BY id"):
        entry = {"g": row["greek"], "e": row["english"], "p": row["part_of_speech"]}
        if row["article"]:
            entry["a"] = row["article"]
        if row["category"]:
            entry["c"] = row["category"]
        if row["id"] in conj_map:
            entry["conj"] = {
                tense: FlowMap(persons)
                for tense, persons in conj_map[row["id"]].items()
            }
        entries.append(entry)

    conn.close()

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        yaml.dump(entries, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    print(f"Exported {len(entries)} words to {OUT_PATH}")


if __name__ == "__main__":
    main()
