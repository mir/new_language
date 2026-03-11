# Greek B1 Vocabulary Project

## Project Overview

SQLite-based Greek vocabulary database targeting CEFR B1 level with verb conjugations.

## Key Paths

- `db/greek_b1.db` — main SQLite database (2172 words, 2706 conjugations)
- `db/conjugation_cache/` — cached Cooljugator HTML pages
- `scripts/` — database creation and population scripts

## Database Schema

```sql
words (id, greek, english, part_of_speech, article, category, notes)
conjugations (id, word_id, tense, person, conjugation)
examples (id, word_id, greek_sentence, english_sentence)
```

## Commands

```bash
# Query the database
sqlite3 db/greek_b1.db "SELECT greek, english FROM words WHERE category='food';"

# Run scripts (always use uv run, never python3)
uv run scripts/create_db.py
uv run scripts/compile_vocabulary.py
uv run scripts/scrape_conjugations.py
uv run scripts/verify_db.py
```

## Conventions

- All Python scripts use inline `uv` dependencies — no virtualenv needed
- Use `uv run --directory` instead of `cd && uv run`
- Conjugation cache files are gitignored; the DB is the source of truth
- Greek nouns should include their article (ο/η/το)
- Verb conjugations cover 3 tenses (present, past/aorist, future) x 6 persons

## Adding Words Workflow

When adding words to the database:
1. **Check for duplicates** — query `SELECT id FROM words WHERE greek = '...'` before inserting
2. **For verbs** — always fetch conjugations from Cooljugator (`https://cooljugator.com/gr/<verb>`) and add all 3 tenses (present, past, future) × 6 persons to the `conjugations` table
3. Use the base/dictionary form (e.g. masculine singular for adjectives, infinitive for verbs)
4. **When displaying verbs** — always show all 3 tenses (present / past / future) in a compact format on one line, e.g. `δοκιμάζω / δοκίμασα / θα δοκιμάσω`
