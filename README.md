# Greek B1 Vocabulary Database

A comprehensive SQLite database of Greek vocabulary targeting CEFR B1 level, with verb conjugation tables.

## What's Inside

- **2,172 words** across all parts of speech (nouns, verbs, adjectives, adverbs, pronouns, conjunctions, prepositions, phrases)
- **580 curated B1 words** with articles, topic categories, and part-of-speech tags covering 25+ CEFR B1 topics
- **1,592 additional words** from the Duolingo Greek vocabulary tree
- **2,706 verb conjugation entries** (present, past/aorist, future) for 153 verbs, scraped from Cooljugator
- **Example sentences table** ready for future population (3 sentences per word)

### Topic Coverage

Personal identification, family, relationships, home, daily life, food & restaurants, shopping, travel & transport, health & body, education, work, entertainment, sports, weather, nature, technology, media, social issues, emotions & opinions, clothing, colors, numbers, time, places, greetings.

## Database Schema

```sql
words (id, greek, english, part_of_speech, article, category, notes)
conjugations (id, word_id, tense, person, conjugation)
examples (id, word_id, greek_sentence, english_sentence)
```

- Nouns include their article (ο/η/το)
- Verbs have conjugations for 6 persons (1s, 2s, 3s, 1p, 2p, 3p) across 3 tenses

## Usage

All scripts use `uv run` with inline dependencies — no virtual environment setup needed.

```bash
# 1. Create the database
uv run scripts/create_db.py

# 2. Populate vocabulary
uv run scripts/compile_vocabulary.py

# 3. Scrape verb conjugations (takes ~6 min with rate limiting)
uv run scripts/scrape_conjugations.py

# 4. Verify the result
uv run scripts/verify_db.py
```

### Quick Queries

```bash
# Count all words
sqlite3 db/greek_b1.db "SELECT COUNT(*) FROM words;"

# List food vocabulary
sqlite3 db/greek_b1.db "SELECT greek, english FROM words WHERE category='food';"

# Get conjugations for a verb
sqlite3 db/greek_b1.db "
  SELECT c.tense, c.person, c.conjugation
  FROM conjugations c JOIN words w ON c.word_id = w.id
  WHERE w.greek = 'γράφω' ORDER BY c.tense, c.person;"

# Words by part of speech
sqlite3 db/greek_b1.db "SELECT part_of_speech, COUNT(*) FROM words GROUP BY part_of_speech ORDER BY COUNT(*) DESC;"
```

## Data Sources

- [kmlawson/greek-vocab](https://github.com/kmlawson/greek-vocab) — ~1,850 words from the Duolingo Greek tree
- [Cooljugator](https://cooljugator.com/gr/) — verb conjugation tables
- Curated B1 vocabulary supplement covering CEFR B1 topics

## File Structure

```
db/
  greek_b1.db              # SQLite database
  conjugation_cache/       # Cached HTML from Cooljugator
scripts/
  create_db.py             # Creates empty DB with schema
  compile_vocabulary.py    # Compiles all vocab sources into DB
  scrape_conjugations.py   # Fetches verb conjugations
  verify_db.py             # Prints stats and quality checks
```
