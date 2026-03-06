#!/usr/bin/env -S uv run --script
# /// script
# dependencies = ["requests<3"]
# requires-python = ">=3.12"
# ///

"""Compiles Greek B1 vocabulary from multiple sources into the SQLite database."""

import re
import sqlite3
from pathlib import Path

import requests

DB_PATH = Path(__file__).parent.parent / "db" / "greek_b1.db"

DUOLINGO_URL = "https://raw.githubusercontent.com/kmlawson/greek-vocab/master/list-flat.txt"


def fetch_duolingo_vocab() -> list[dict]:
    """Download and parse the Duolingo Greek vocab list."""
    print("Fetching Duolingo Greek vocab list...")
    resp = requests.get(DUOLINGO_URL, timeout=30)
    resp.raise_for_status()

    words = []
    for line in resp.text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Format: "greek - english" or "greek\tenglish" variations
        parts = re.split(r"\s*[-–—]\s*|\t+", line, maxsplit=1)
        if len(parts) == 2:
            greek = parts[0].strip()
            english = parts[1].strip()
            if greek and english:
                words.append({"greek": greek, "english": english})
    print(f"  Parsed {len(words)} words from Duolingo list")
    return words


def get_curated_b1_vocabulary() -> list[dict]:
    """Curated B1-level vocabulary covering all CEFR B1 topics."""
    return [
        # ===== Personal identification, family, relationships =====
        {"greek": "η ταυτότητα", "english": "identity/ID card", "pos": "noun", "article": "η", "category": "personal"},
        {"greek": "το διαβατήριο", "english": "passport", "pos": "noun", "article": "το", "category": "personal"},
        {"greek": "η διεύθυνση", "english": "address", "pos": "noun", "article": "η", "category": "personal"},
        {"greek": "η υπηκοότητα", "english": "nationality/citizenship", "pos": "noun", "article": "η", "category": "personal"},
        {"greek": "η ηλικία", "english": "age", "pos": "noun", "article": "η", "category": "personal"},
        {"greek": "το επάγγελμα", "english": "profession", "pos": "noun", "article": "το", "category": "personal"},
        {"greek": "ο σύζυγος", "english": "husband/spouse", "pos": "noun", "article": "ο", "category": "family"},
        {"greek": "η σύζυγος", "english": "wife/spouse", "pos": "noun", "article": "η", "category": "family"},
        {"greek": "ο αδερφός", "english": "brother", "pos": "noun", "article": "ο", "category": "family"},
        {"greek": "η αδερφή", "english": "sister", "pos": "noun", "article": "η", "category": "family"},
        {"greek": "ο παππούς", "english": "grandfather", "pos": "noun", "article": "ο", "category": "family"},
        {"greek": "η γιαγιά", "english": "grandmother", "pos": "noun", "article": "η", "category": "family"},
        {"greek": "ο θείος", "english": "uncle", "pos": "noun", "article": "ο", "category": "family"},
        {"greek": "η θεία", "english": "aunt", "pos": "noun", "article": "η", "category": "family"},
        {"greek": "ο ξάδερφος", "english": "cousin (male)", "pos": "noun", "article": "ο", "category": "family"},
        {"greek": "η ξαδέρφη", "english": "cousin (female)", "pos": "noun", "article": "η", "category": "family"},
        {"greek": "ο γαμπρός", "english": "groom/son-in-law", "pos": "noun", "article": "ο", "category": "family"},
        {"greek": "η νύφη", "english": "bride/daughter-in-law", "pos": "noun", "article": "η", "category": "family"},
        {"greek": "ο γείτονας", "english": "neighbor", "pos": "noun", "article": "ο", "category": "relationships"},
        {"greek": "η σχέση", "english": "relationship", "pos": "noun", "article": "η", "category": "relationships"},
        {"greek": "η φιλία", "english": "friendship", "pos": "noun", "article": "η", "category": "relationships"},
        {"greek": "ο γάμος", "english": "wedding/marriage", "pos": "noun", "article": "ο", "category": "relationships"},
        {"greek": "το διαζύγιο", "english": "divorce", "pos": "noun", "article": "το", "category": "relationships"},
        {"greek": "παντρεύομαι", "english": "to get married", "pos": "verb", "category": "relationships"},
        {"greek": "χωρίζω", "english": "to break up/separate", "pos": "verb", "category": "relationships"},

        # ===== Home, housing, environment =====
        {"greek": "το σπίτι", "english": "house/home", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "το διαμέρισμα", "english": "apartment", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "το δωμάτιο", "english": "room", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "η κουζίνα", "english": "kitchen", "pos": "noun", "article": "η", "category": "home"},
        {"greek": "το μπάνιο", "english": "bathroom", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "το υπνοδωμάτιο", "english": "bedroom", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "το σαλόνι", "english": "living room", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "η αυλή", "english": "yard/courtyard", "pos": "noun", "article": "η", "category": "home"},
        {"greek": "το μπαλκόνι", "english": "balcony", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "ο όροφος", "english": "floor/story", "pos": "noun", "article": "ο", "category": "home"},
        {"greek": "η σκάλα", "english": "stairs/ladder", "pos": "noun", "article": "η", "category": "home"},
        {"greek": "το ασανσέρ", "english": "elevator", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "η πόρτα", "english": "door", "pos": "noun", "article": "η", "category": "home"},
        {"greek": "το παράθυρο", "english": "window", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "ο τοίχος", "english": "wall", "pos": "noun", "article": "ο", "category": "home"},
        {"greek": "το πάτωμα", "english": "floor", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "η οροφή", "english": "ceiling/roof", "pos": "noun", "article": "η", "category": "home"},
        {"greek": "το κλειδί", "english": "key", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "το ενοίκιο", "english": "rent", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "ο ιδιοκτήτης", "english": "owner/landlord", "pos": "noun", "article": "ο", "category": "home"},
        {"greek": "ο ενοικιαστής", "english": "tenant", "pos": "noun", "article": "ο", "category": "home"},
        {"greek": "νοικιάζω", "english": "to rent", "pos": "verb", "category": "home"},
        {"greek": "μετακομίζω", "english": "to move (house)", "pos": "verb", "category": "home"},
        {"greek": "καθαρίζω", "english": "to clean", "pos": "verb", "category": "home"},
        {"greek": "επισκευάζω", "english": "to repair", "pos": "verb", "category": "home"},

        # ===== Furniture & household =====
        {"greek": "το τραπέζι", "english": "table", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "η καρέκλα", "english": "chair", "pos": "noun", "article": "η", "category": "home"},
        {"greek": "ο καναπές", "english": "sofa/couch", "pos": "noun", "article": "ο", "category": "home"},
        {"greek": "το κρεβάτι", "english": "bed", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "η ντουλάπα", "english": "wardrobe", "pos": "noun", "article": "η", "category": "home"},
        {"greek": "το ψυγείο", "english": "refrigerator", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "η κουρτίνα", "english": "curtain", "pos": "noun", "article": "η", "category": "home"},
        {"greek": "ο καθρέφτης", "english": "mirror", "pos": "noun", "article": "ο", "category": "home"},
        {"greek": "το φως", "english": "light", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "η λάμπα", "english": "lamp", "pos": "noun", "article": "η", "category": "home"},
        {"greek": "το πλυντήριο", "english": "washing machine", "pos": "noun", "article": "το", "category": "home"},
        {"greek": "η ηλεκτρική σκούπα", "english": "vacuum cleaner", "pos": "noun", "article": "η", "category": "home"},

        # ===== Daily life, routines =====
        {"greek": "ξυπνάω", "english": "to wake up", "pos": "verb", "category": "daily_life"},
        {"greek": "σηκώνομαι", "english": "to get up", "pos": "verb", "category": "daily_life"},
        {"greek": "πλένομαι", "english": "to wash oneself", "pos": "verb", "category": "daily_life"},
        {"greek": "ντύνομαι", "english": "to get dressed", "pos": "verb", "category": "daily_life"},
        {"greek": "χτενίζομαι", "english": "to comb one's hair", "pos": "verb", "category": "daily_life"},
        {"greek": "βουρτσίζω", "english": "to brush (teeth)", "pos": "verb", "category": "daily_life"},
        {"greek": "μαγειρεύω", "english": "to cook", "pos": "verb", "category": "daily_life"},
        {"greek": "πλένω", "english": "to wash", "pos": "verb", "category": "daily_life"},
        {"greek": "σιδερώνω", "english": "to iron", "pos": "verb", "category": "daily_life"},
        {"greek": "κοιμάμαι", "english": "to sleep", "pos": "verb", "category": "daily_life"},
        {"greek": "ξεκουράζομαι", "english": "to rest", "pos": "verb", "category": "daily_life"},
        {"greek": "η ρουτίνα", "english": "routine", "pos": "noun", "article": "η", "category": "daily_life"},
        {"greek": "η συνήθεια", "english": "habit", "pos": "noun", "article": "η", "category": "daily_life"},
        {"greek": "το πρωινό", "english": "breakfast", "pos": "noun", "article": "το", "category": "daily_life"},
        {"greek": "το μεσημεριανό", "english": "lunch", "pos": "noun", "article": "το", "category": "daily_life"},
        {"greek": "το βραδινό", "english": "dinner", "pos": "noun", "article": "το", "category": "daily_life"},

        # ===== Food, drink, restaurants =====
        {"greek": "το ψωμί", "english": "bread", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το κρέας", "english": "meat", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το κοτόπουλο", "english": "chicken", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το ψάρι", "english": "fish", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το ρύζι", "english": "rice", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "τα ζυμαρικά", "english": "pasta", "pos": "noun", "article": "τα", "category": "food"},
        {"greek": "η σαλάτα", "english": "salad", "pos": "noun", "article": "η", "category": "food"},
        {"greek": "το τυρί", "english": "cheese", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το αυγό", "english": "egg", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το γάλα", "english": "milk", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το βούτυρο", "english": "butter", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το λάδι", "english": "oil", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το αλάτι", "english": "salt", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το πιπέρι", "english": "pepper", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "η ζάχαρη", "english": "sugar", "pos": "noun", "article": "η", "category": "food"},
        {"greek": "το μήλο", "english": "apple", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "η μπανάνα", "english": "banana", "pos": "noun", "article": "η", "category": "food"},
        {"greek": "το πορτοκάλι", "english": "orange", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "η ντομάτα", "english": "tomato", "pos": "noun", "article": "η", "category": "food"},
        {"greek": "το αγγούρι", "english": "cucumber", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "η πατάτα", "english": "potato", "pos": "noun", "article": "η", "category": "food"},
        {"greek": "το κρεμμύδι", "english": "onion", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το σκόρδο", "english": "garlic", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "ο καφές", "english": "coffee", "pos": "noun", "article": "ο", "category": "food"},
        {"greek": "το τσάι", "english": "tea", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το νερό", "english": "water", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "ο χυμός", "english": "juice", "pos": "noun", "article": "ο", "category": "food"},
        {"greek": "το κρασί", "english": "wine", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "η μπύρα", "english": "beer", "pos": "noun", "article": "η", "category": "food"},
        {"greek": "το εστιατόριο", "english": "restaurant", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "η ταβέρνα", "english": "taverna", "pos": "noun", "article": "η", "category": "food"},
        {"greek": "το καφενείο", "english": "cafe", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "ο λογαριασμός", "english": "bill/account", "pos": "noun", "article": "ο", "category": "food"},
        {"greek": "το μενού", "english": "menu", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το πιάτο", "english": "plate/dish", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το ποτήρι", "english": "glass", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το μαχαίρι", "english": "knife", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το πιρούνι", "english": "fork", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "το κουτάλι", "english": "spoon", "pos": "noun", "article": "το", "category": "food"},
        {"greek": "παραγγέλνω", "english": "to order", "pos": "verb", "category": "food"},
        {"greek": "πληρώνω", "english": "to pay", "pos": "verb", "category": "food"},
        {"greek": "τρώω", "english": "to eat", "pos": "verb", "category": "food"},
        {"greek": "πίνω", "english": "to drink", "pos": "verb", "category": "food"},
        {"greek": "δοκιμάζω", "english": "to try/taste", "pos": "verb", "category": "food"},

        # ===== Shopping, prices =====
        {"greek": "το μαγαζί", "english": "shop/store", "pos": "noun", "article": "το", "category": "shopping"},
        {"greek": "η αγορά", "english": "market/purchase", "pos": "noun", "article": "η", "category": "shopping"},
        {"greek": "το σούπερ μάρκετ", "english": "supermarket", "pos": "noun", "article": "το", "category": "shopping"},
        {"greek": "το εμπορικό κέντρο", "english": "shopping mall", "pos": "noun", "article": "το", "category": "shopping"},
        {"greek": "η τιμή", "english": "price", "pos": "noun", "article": "η", "category": "shopping"},
        {"greek": "η έκπτωση", "english": "discount", "pos": "noun", "article": "η", "category": "shopping"},
        {"greek": "η προσφορά", "english": "offer/deal", "pos": "noun", "article": "η", "category": "shopping"},
        {"greek": "το ταμείο", "english": "cash register/fund", "pos": "noun", "article": "το", "category": "shopping"},
        {"greek": "η απόδειξη", "english": "receipt", "pos": "noun", "article": "η", "category": "shopping"},
        {"greek": "τα ρέστα", "english": "change (money)", "pos": "noun", "article": "τα", "category": "shopping"},
        {"greek": "η κάρτα", "english": "card", "pos": "noun", "article": "η", "category": "shopping"},
        {"greek": "τα μετρητά", "english": "cash", "pos": "noun", "article": "τα", "category": "shopping"},
        {"greek": "αγοράζω", "english": "to buy", "pos": "verb", "category": "shopping"},
        {"greek": "πουλάω", "english": "to sell", "pos": "verb", "category": "shopping"},
        {"greek": "κοστίζω", "english": "to cost", "pos": "verb", "category": "shopping"},
        {"greek": "ακριβός", "english": "expensive", "pos": "adjective", "category": "shopping"},
        {"greek": "φτηνός", "english": "cheap", "pos": "adjective", "category": "shopping"},
        {"greek": "δωρεάν", "english": "free (no cost)", "pos": "adverb", "category": "shopping"},

        # ===== Travel, transport, tourism =====
        {"greek": "το αεροπλάνο", "english": "airplane", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "το αεροδρόμιο", "english": "airport", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "το τρένο", "english": "train", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "ο σταθμός", "english": "station", "pos": "noun", "article": "ο", "category": "travel"},
        {"greek": "το λεωφορείο", "english": "bus", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "η στάση", "english": "stop (bus/tram)", "pos": "noun", "article": "η", "category": "travel"},
        {"greek": "το μετρό", "english": "metro/subway", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "το ταξί", "english": "taxi", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "το πλοίο", "english": "ship/boat", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "το λιμάνι", "english": "port/harbor", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "το αυτοκίνητο", "english": "car", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "το ποδήλατο", "english": "bicycle", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "ο δρόμος", "english": "road/street", "pos": "noun", "article": "ο", "category": "travel"},
        {"greek": "η γέφυρα", "english": "bridge", "pos": "noun", "article": "η", "category": "travel"},
        {"greek": "το εισιτήριο", "english": "ticket", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "η βαλίτσα", "english": "suitcase", "pos": "noun", "article": "η", "category": "travel"},
        {"greek": "το ξενοδοχείο", "english": "hotel", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "η κράτηση", "english": "reservation", "pos": "noun", "article": "η", "category": "travel"},
        {"greek": "ο χάρτης", "english": "map", "pos": "noun", "article": "ο", "category": "travel"},
        {"greek": "ο τουρίστας", "english": "tourist", "pos": "noun", "article": "ο", "category": "travel"},
        {"greek": "η παραλία", "english": "beach", "pos": "noun", "article": "η", "category": "travel"},
        {"greek": "το νησί", "english": "island", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "το μουσείο", "english": "museum", "pos": "noun", "article": "το", "category": "travel"},
        {"greek": "ο ναός", "english": "temple/church", "pos": "noun", "article": "ο", "category": "travel"},
        {"greek": "ταξιδεύω", "english": "to travel", "pos": "verb", "category": "travel"},
        {"greek": "φτάνω", "english": "to arrive", "pos": "verb", "category": "travel"},
        {"greek": "φεύγω", "english": "to leave/depart", "pos": "verb", "category": "travel"},
        {"greek": "επιστρέφω", "english": "to return", "pos": "verb", "category": "travel"},
        {"greek": "οδηγώ", "english": "to drive", "pos": "verb", "category": "travel"},
        {"greek": "περπατάω", "english": "to walk", "pos": "verb", "category": "travel"},
        {"greek": "επισκέπτομαι", "english": "to visit", "pos": "verb", "category": "travel"},

        # ===== Health, body, medical =====
        {"greek": "το κεφάλι", "english": "head", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "τα μάτια", "english": "eyes", "pos": "noun", "article": "τα", "category": "health"},
        {"greek": "τα αυτιά", "english": "ears", "pos": "noun", "article": "τα", "category": "health"},
        {"greek": "η μύτη", "english": "nose", "pos": "noun", "article": "η", "category": "health"},
        {"greek": "το στόμα", "english": "mouth", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "τα δόντια", "english": "teeth", "pos": "noun", "article": "τα", "category": "health"},
        {"greek": "ο λαιμός", "english": "neck/throat", "pos": "noun", "article": "ο", "category": "health"},
        {"greek": "ο ώμος", "english": "shoulder", "pos": "noun", "article": "ο", "category": "health"},
        {"greek": "το χέρι", "english": "hand/arm", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "το δάχτυλο", "english": "finger", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "η πλάτη", "english": "back", "pos": "noun", "article": "η", "category": "health"},
        {"greek": "η κοιλιά", "english": "belly/stomach", "pos": "noun", "article": "η", "category": "health"},
        {"greek": "το πόδι", "english": "leg/foot", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "το γόνατο", "english": "knee", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "η καρδιά", "english": "heart", "pos": "noun", "article": "η", "category": "health"},
        {"greek": "ο πόνος", "english": "pain", "pos": "noun", "article": "ο", "category": "health"},
        {"greek": "ο πυρετός", "english": "fever", "pos": "noun", "article": "ο", "category": "health"},
        {"greek": "ο βήχας", "english": "cough", "pos": "noun", "article": "ο", "category": "health"},
        {"greek": "το κρυολόγημα", "english": "cold (illness)", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "η γρίπη", "english": "flu", "pos": "noun", "article": "η", "category": "health"},
        {"greek": "η αλλεργία", "english": "allergy", "pos": "noun", "article": "η", "category": "health"},
        {"greek": "το φάρμακο", "english": "medicine/drug", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "το νοσοκομείο", "english": "hospital", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "ο γιατρός", "english": "doctor", "pos": "noun", "article": "ο", "category": "health"},
        {"greek": "ο οδοντίατρος", "english": "dentist", "pos": "noun", "article": "ο", "category": "health"},
        {"greek": "το φαρμακείο", "english": "pharmacy", "pos": "noun", "article": "το", "category": "health"},
        {"greek": "η ασθένεια", "english": "illness/disease", "pos": "noun", "article": "η", "category": "health"},
        {"greek": "η υγεία", "english": "health", "pos": "noun", "article": "η", "category": "health"},
        {"greek": "η συνταγή", "english": "prescription/recipe", "pos": "noun", "article": "η", "category": "health"},
        {"greek": "πονάω", "english": "to hurt/ache", "pos": "verb", "category": "health"},
        {"greek": "αρρωσταίνω", "english": "to get sick", "pos": "verb", "category": "health"},
        {"greek": "θεραπεύω", "english": "to cure/treat", "pos": "verb", "category": "health"},
        {"greek": "εξετάζω", "english": "to examine", "pos": "verb", "category": "health"},

        # ===== Education, school, work =====
        {"greek": "το σχολείο", "english": "school", "pos": "noun", "article": "το", "category": "education"},
        {"greek": "το πανεπιστήμιο", "english": "university", "pos": "noun", "article": "το", "category": "education"},
        {"greek": "η τάξη", "english": "class/classroom", "pos": "noun", "article": "η", "category": "education"},
        {"greek": "το μάθημα", "english": "lesson/course", "pos": "noun", "article": "το", "category": "education"},
        {"greek": "ο καθηγητής", "english": "professor/teacher", "pos": "noun", "article": "ο", "category": "education"},
        {"greek": "ο μαθητής", "english": "student (school)", "pos": "noun", "article": "ο", "category": "education"},
        {"greek": "ο φοιτητής", "english": "student (university)", "pos": "noun", "article": "ο", "category": "education"},
        {"greek": "η εξέταση", "english": "exam", "pos": "noun", "article": "η", "category": "education"},
        {"greek": "ο βαθμός", "english": "grade/degree", "pos": "noun", "article": "ο", "category": "education"},
        {"greek": "το πτυχίο", "english": "degree/diploma", "pos": "noun", "article": "το", "category": "education"},
        {"greek": "η βιβλιοθήκη", "english": "library", "pos": "noun", "article": "η", "category": "education"},
        {"greek": "το βιβλίο", "english": "book", "pos": "noun", "article": "το", "category": "education"},
        {"greek": "το τετράδιο", "english": "notebook", "pos": "noun", "article": "το", "category": "education"},
        {"greek": "το στυλό", "english": "pen", "pos": "noun", "article": "το", "category": "education"},
        {"greek": "μαθαίνω", "english": "to learn", "pos": "verb", "category": "education"},
        {"greek": "διδάσκω", "english": "to teach", "pos": "verb", "category": "education"},
        {"greek": "σπουδάζω", "english": "to study (university)", "pos": "verb", "category": "education"},
        {"greek": "διαβάζω", "english": "to read/study", "pos": "verb", "category": "education"},
        {"greek": "γράφω", "english": "to write", "pos": "verb", "category": "education"},
        {"greek": "εξετάζομαι", "english": "to take an exam", "pos": "verb", "category": "education"},
        {"greek": "η δουλειά", "english": "work/job", "pos": "noun", "article": "η", "category": "work"},
        {"greek": "το γραφείο", "english": "office/desk", "pos": "noun", "article": "το", "category": "work"},
        {"greek": "η εταιρεία", "english": "company", "pos": "noun", "article": "η", "category": "work"},
        {"greek": "ο μισθός", "english": "salary", "pos": "noun", "article": "ο", "category": "work"},
        {"greek": "η σύμβαση", "english": "contract", "pos": "noun", "article": "η", "category": "work"},
        {"greek": "η συνέντευξη", "english": "interview", "pos": "noun", "article": "η", "category": "work"},
        {"greek": "το βιογραφικό", "english": "CV/resume", "pos": "noun", "article": "το", "category": "work"},
        {"greek": "η άδεια", "english": "leave/permit/license", "pos": "noun", "article": "η", "category": "work"},
        {"greek": "η σύνταξη", "english": "pension/retirement", "pos": "noun", "article": "η", "category": "work"},
        {"greek": "ο συνάδελφος", "english": "colleague", "pos": "noun", "article": "ο", "category": "work"},
        {"greek": "ο διευθυντής", "english": "director/manager", "pos": "noun", "article": "ο", "category": "work"},
        {"greek": "δουλεύω", "english": "to work", "pos": "verb", "category": "work"},
        {"greek": "προσλαμβάνω", "english": "to hire", "pos": "verb", "category": "work"},
        {"greek": "απολύω", "english": "to fire/dismiss", "pos": "verb", "category": "work"},
        {"greek": "συνεργάζομαι", "english": "to cooperate/collaborate", "pos": "verb", "category": "work"},

        # ===== Free time, entertainment, sports =====
        {"greek": "η μουσική", "english": "music", "pos": "noun", "article": "η", "category": "entertainment"},
        {"greek": "ο κινηματογράφος", "english": "cinema", "pos": "noun", "article": "ο", "category": "entertainment"},
        {"greek": "η ταινία", "english": "movie/film", "pos": "noun", "article": "η", "category": "entertainment"},
        {"greek": "το θέατρο", "english": "theater", "pos": "noun", "article": "το", "category": "entertainment"},
        {"greek": "η παράσταση", "english": "performance/show", "pos": "noun", "article": "η", "category": "entertainment"},
        {"greek": "η συναυλία", "english": "concert", "pos": "noun", "article": "η", "category": "entertainment"},
        {"greek": "το τραγούδι", "english": "song", "pos": "noun", "article": "το", "category": "entertainment"},
        {"greek": "ο χορός", "english": "dance", "pos": "noun", "article": "ο", "category": "entertainment"},
        {"greek": "η ζωγραφική", "english": "painting", "pos": "noun", "article": "η", "category": "entertainment"},
        {"greek": "η φωτογραφία", "english": "photography/photo", "pos": "noun", "article": "η", "category": "entertainment"},
        {"greek": "το χόμπι", "english": "hobby", "pos": "noun", "article": "το", "category": "entertainment"},
        {"greek": "το ποδόσφαιρο", "english": "football/soccer", "pos": "noun", "article": "το", "category": "sports"},
        {"greek": "το μπάσκετ", "english": "basketball", "pos": "noun", "article": "το", "category": "sports"},
        {"greek": "η κολύμβηση", "english": "swimming", "pos": "noun", "article": "η", "category": "sports"},
        {"greek": "το τρέξιμο", "english": "running", "pos": "noun", "article": "το", "category": "sports"},
        {"greek": "η γυμναστική", "english": "exercise/gymnastics", "pos": "noun", "article": "η", "category": "sports"},
        {"greek": "το γυμναστήριο", "english": "gym", "pos": "noun", "article": "το", "category": "sports"},
        {"greek": "ο αγώνας", "english": "match/competition", "pos": "noun", "article": "ο", "category": "sports"},
        {"greek": "η ομάδα", "english": "team", "pos": "noun", "article": "η", "category": "sports"},
        {"greek": "η νίκη", "english": "victory", "pos": "noun", "article": "η", "category": "sports"},
        {"greek": "η ήττα", "english": "defeat", "pos": "noun", "article": "η", "category": "sports"},
        {"greek": "τραγουδάω", "english": "to sing", "pos": "verb", "category": "entertainment"},
        {"greek": "χορεύω", "english": "to dance", "pos": "verb", "category": "entertainment"},
        {"greek": "παίζω", "english": "to play", "pos": "verb", "category": "entertainment"},
        {"greek": "κολυμπάω", "english": "to swim", "pos": "verb", "category": "sports"},
        {"greek": "τρέχω", "english": "to run", "pos": "verb", "category": "sports"},
        {"greek": "γυμνάζομαι", "english": "to exercise", "pos": "verb", "category": "sports"},
        {"greek": "κερδίζω", "english": "to win", "pos": "verb", "category": "sports"},
        {"greek": "χάνω", "english": "to lose", "pos": "verb", "category": "sports"},

        # ===== Weather, nature, environment =====
        {"greek": "ο ήλιος", "english": "sun", "pos": "noun", "article": "ο", "category": "weather"},
        {"greek": "η βροχή", "english": "rain", "pos": "noun", "article": "η", "category": "weather"},
        {"greek": "το χιόνι", "english": "snow", "pos": "noun", "article": "το", "category": "weather"},
        {"greek": "ο αέρας", "english": "wind/air", "pos": "noun", "article": "ο", "category": "weather"},
        {"greek": "η θύελλα", "english": "storm", "pos": "noun", "article": "η", "category": "weather"},
        {"greek": "το σύννεφο", "english": "cloud", "pos": "noun", "article": "το", "category": "weather"},
        {"greek": "η ομίχλη", "english": "fog", "pos": "noun", "article": "η", "category": "weather"},
        {"greek": "η θερμοκρασία", "english": "temperature", "pos": "noun", "article": "η", "category": "weather"},
        {"greek": "ο ουρανός", "english": "sky", "pos": "noun", "article": "ο", "category": "weather"},
        {"greek": "το δέντρο", "english": "tree", "pos": "noun", "article": "το", "category": "nature"},
        {"greek": "το λουλούδι", "english": "flower", "pos": "noun", "article": "το", "category": "nature"},
        {"greek": "το βουνό", "english": "mountain", "pos": "noun", "article": "το", "category": "nature"},
        {"greek": "η θάλασσα", "english": "sea", "pos": "noun", "article": "η", "category": "nature"},
        {"greek": "το ποτάμι", "english": "river", "pos": "noun", "article": "το", "category": "nature"},
        {"greek": "η λίμνη", "english": "lake", "pos": "noun", "article": "η", "category": "nature"},
        {"greek": "το δάσος", "english": "forest", "pos": "noun", "article": "το", "category": "nature"},
        {"greek": "η φύση", "english": "nature", "pos": "noun", "article": "η", "category": "nature"},
        {"greek": "το ζώο", "english": "animal", "pos": "noun", "article": "το", "category": "nature"},
        {"greek": "ο σκύλος", "english": "dog", "pos": "noun", "article": "ο", "category": "nature"},
        {"greek": "η γάτα", "english": "cat", "pos": "noun", "article": "η", "category": "nature"},
        {"greek": "το πουλί", "english": "bird", "pos": "noun", "article": "το", "category": "nature"},
        {"greek": "το περιβάλλον", "english": "environment", "pos": "noun", "article": "το", "category": "nature"},
        {"greek": "η ρύπανση", "english": "pollution", "pos": "noun", "article": "η", "category": "nature"},
        {"greek": "η ανακύκλωση", "english": "recycling", "pos": "noun", "article": "η", "category": "nature"},
        {"greek": "βρέχει", "english": "it rains", "pos": "verb", "category": "weather"},
        {"greek": "χιονίζει", "english": "it snows", "pos": "verb", "category": "weather"},
        {"greek": "φυσάει", "english": "it's windy", "pos": "verb", "category": "weather"},
        {"greek": "ζεσταίνω", "english": "to heat/warm", "pos": "verb", "category": "weather"},
        {"greek": "κρυώνω", "english": "to feel cold", "pos": "verb", "category": "weather"},

        # ===== Media, technology, communication =====
        {"greek": "ο υπολογιστής", "english": "computer", "pos": "noun", "article": "ο", "category": "technology"},
        {"greek": "το κινητό", "english": "mobile phone", "pos": "noun", "article": "το", "category": "technology"},
        {"greek": "το διαδίκτυο", "english": "internet", "pos": "noun", "article": "το", "category": "technology"},
        {"greek": "η ιστοσελίδα", "english": "website", "pos": "noun", "article": "η", "category": "technology"},
        {"greek": "το ηλεκτρονικό ταχυδρομείο", "english": "email", "pos": "noun", "article": "το", "category": "technology"},
        {"greek": "το μήνυμα", "english": "message", "pos": "noun", "article": "το", "category": "technology"},
        {"greek": "η εφαρμογή", "english": "application/app", "pos": "noun", "article": "η", "category": "technology"},
        {"greek": "η οθόνη", "english": "screen", "pos": "noun", "article": "η", "category": "technology"},
        {"greek": "το πληκτρολόγιο", "english": "keyboard", "pos": "noun", "article": "το", "category": "technology"},
        {"greek": "η εφημερίδα", "english": "newspaper", "pos": "noun", "article": "η", "category": "media"},
        {"greek": "το περιοδικό", "english": "magazine", "pos": "noun", "article": "το", "category": "media"},
        {"greek": "η τηλεόραση", "english": "television", "pos": "noun", "article": "η", "category": "media"},
        {"greek": "το ραδιόφωνο", "english": "radio", "pos": "noun", "article": "το", "category": "media"},
        {"greek": "η είδηση", "english": "news (item)", "pos": "noun", "article": "η", "category": "media"},
        {"greek": "η διαφήμιση", "english": "advertisement", "pos": "noun", "article": "η", "category": "media"},
        {"greek": "τηλεφωνώ", "english": "to call/phone", "pos": "verb", "category": "technology"},
        {"greek": "στέλνω", "english": "to send", "pos": "verb", "category": "technology"},
        {"greek": "λαμβάνω", "english": "to receive", "pos": "verb", "category": "technology"},
        {"greek": "κατεβάζω", "english": "to download", "pos": "verb", "category": "technology"},
        {"greek": "ανεβάζω", "english": "to upload", "pos": "verb", "category": "technology"},

        # ===== Social issues, current affairs =====
        {"greek": "η κοινωνία", "english": "society", "pos": "noun", "article": "η", "category": "social"},
        {"greek": "η κυβέρνηση", "english": "government", "pos": "noun", "article": "η", "category": "social"},
        {"greek": "η πολιτική", "english": "politics/policy", "pos": "noun", "article": "η", "category": "social"},
        {"greek": "η οικονομία", "english": "economy", "pos": "noun", "article": "η", "category": "social"},
        {"greek": "η ανεργία", "english": "unemployment", "pos": "noun", "article": "η", "category": "social"},
        {"greek": "η μετανάστευση", "english": "immigration", "pos": "noun", "article": "η", "category": "social"},
        {"greek": "το δικαίωμα", "english": "right (legal)", "pos": "noun", "article": "το", "category": "social"},
        {"greek": "η ελευθερία", "english": "freedom", "pos": "noun", "article": "η", "category": "social"},
        {"greek": "η ειρήνη", "english": "peace", "pos": "noun", "article": "η", "category": "social"},
        {"greek": "ο πόλεμος", "english": "war", "pos": "noun", "article": "ο", "category": "social"},
        {"greek": "η εκλογή", "english": "election", "pos": "noun", "article": "η", "category": "social"},
        {"greek": "ο νόμος", "english": "law", "pos": "noun", "article": "ο", "category": "social"},
        {"greek": "ψηφίζω", "english": "to vote", "pos": "verb", "category": "social"},
        {"greek": "διαμαρτύρομαι", "english": "to protest", "pos": "verb", "category": "social"},

        # ===== Feelings, opinions, emotions =====
        {"greek": "η χαρά", "english": "joy/happiness", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "η λύπη", "english": "sadness/sorrow", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "ο θυμός", "english": "anger", "pos": "noun", "article": "ο", "category": "emotions"},
        {"greek": "ο φόβος", "english": "fear", "pos": "noun", "article": "ο", "category": "emotions"},
        {"greek": "η αγάπη", "english": "love", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "το μίσος", "english": "hatred", "pos": "noun", "article": "το", "category": "emotions"},
        {"greek": "η έκπληξη", "english": "surprise", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "η ελπίδα", "english": "hope", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "η ανησυχία", "english": "worry/anxiety", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "η ζήλια", "english": "jealousy", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "η περηφάνια", "english": "pride", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "η ντροπή", "english": "shame/embarrassment", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "η γνώμη", "english": "opinion", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "η άποψη", "english": "view/opinion", "pos": "noun", "article": "η", "category": "emotions"},
        {"greek": "αγαπάω", "english": "to love", "pos": "verb", "category": "emotions"},
        {"greek": "μισώ", "english": "to hate", "pos": "verb", "category": "emotions"},
        {"greek": "φοβάμαι", "english": "to fear/be afraid", "pos": "verb", "category": "emotions"},
        {"greek": "χαίρομαι", "english": "to be happy/glad", "pos": "verb", "category": "emotions"},
        {"greek": "στεναχωριέμαι", "english": "to be sad/upset", "pos": "verb", "category": "emotions"},
        {"greek": "θυμώνω", "english": "to get angry", "pos": "verb", "category": "emotions"},
        {"greek": "ελπίζω", "english": "to hope", "pos": "verb", "category": "emotions"},
        {"greek": "ανησυχώ", "english": "to worry", "pos": "verb", "category": "emotions"},
        {"greek": "νομίζω", "english": "to think/believe", "pos": "verb", "category": "emotions"},
        {"greek": "πιστεύω", "english": "to believe", "pos": "verb", "category": "emotions"},
        {"greek": "συμφωνώ", "english": "to agree", "pos": "verb", "category": "emotions"},
        {"greek": "διαφωνώ", "english": "to disagree", "pos": "verb", "category": "emotions"},
        {"greek": "προτιμάω", "english": "to prefer", "pos": "verb", "category": "emotions"},

        # ===== Common adjectives =====
        {"greek": "μεγάλος", "english": "big/large/great", "pos": "adjective", "category": "description"},
        {"greek": "μικρός", "english": "small/little", "pos": "adjective", "category": "description"},
        {"greek": "καλός", "english": "good", "pos": "adjective", "category": "description"},
        {"greek": "κακός", "english": "bad", "pos": "adjective", "category": "description"},
        {"greek": "νέος", "english": "new/young", "pos": "adjective", "category": "description"},
        {"greek": "παλιός", "english": "old (things)", "pos": "adjective", "category": "description"},
        {"greek": "γέρος", "english": "old (people)", "pos": "adjective", "category": "description"},
        {"greek": "ωραίος", "english": "beautiful/nice", "pos": "adjective", "category": "description"},
        {"greek": "άσχημος", "english": "ugly", "pos": "adjective", "category": "description"},
        {"greek": "εύκολος", "english": "easy", "pos": "adjective", "category": "description"},
        {"greek": "δύσκολος", "english": "difficult", "pos": "adjective", "category": "description"},
        {"greek": "γρήγορος", "english": "fast/quick", "pos": "adjective", "category": "description"},
        {"greek": "αργός", "english": "slow", "pos": "adjective", "category": "description"},
        {"greek": "ζεστός", "english": "hot/warm", "pos": "adjective", "category": "description"},
        {"greek": "κρύος", "english": "cold", "pos": "adjective", "category": "description"},
        {"greek": "δυνατός", "english": "strong/loud", "pos": "adjective", "category": "description"},
        {"greek": "αδύναμος", "english": "weak", "pos": "adjective", "category": "description"},
        {"greek": "σημαντικός", "english": "important", "pos": "adjective", "category": "description"},
        {"greek": "απαραίτητος", "english": "necessary", "pos": "adjective", "category": "description"},
        {"greek": "δυνατός", "english": "possible/strong", "pos": "adjective", "category": "description"},
        {"greek": "αδύνατος", "english": "impossible/thin", "pos": "adjective", "category": "description"},
        {"greek": "σωστός", "english": "correct/right", "pos": "adjective", "category": "description"},
        {"greek": "λάθος", "english": "wrong/mistake", "pos": "adjective", "category": "description"},
        {"greek": "ελεύθερος", "english": "free", "pos": "adjective", "category": "description"},
        {"greek": "έτοιμος", "english": "ready", "pos": "adjective", "category": "description"},
        {"greek": "ήσυχος", "english": "quiet/calm", "pos": "adjective", "category": "description"},
        {"greek": "δημόσιος", "english": "public", "pos": "adjective", "category": "description"},
        {"greek": "ιδιωτικός", "english": "private", "pos": "adjective", "category": "description"},

        # ===== Common adverbs =====
        {"greek": "πολύ", "english": "very/much", "pos": "adverb", "category": "description"},
        {"greek": "λίγο", "english": "a little", "pos": "adverb", "category": "description"},
        {"greek": "πάντα", "english": "always", "pos": "adverb", "category": "time"},
        {"greek": "ποτέ", "english": "never", "pos": "adverb", "category": "time"},
        {"greek": "συχνά", "english": "often", "pos": "adverb", "category": "time"},
        {"greek": "σπάνια", "english": "rarely", "pos": "adverb", "category": "time"},
        {"greek": "μερικές φορές", "english": "sometimes", "pos": "adverb", "category": "time"},
        {"greek": "ήδη", "english": "already", "pos": "adverb", "category": "time"},
        {"greek": "ακόμα", "english": "still/yet", "pos": "adverb", "category": "time"},
        {"greek": "τώρα", "english": "now", "pos": "adverb", "category": "time"},
        {"greek": "σήμερα", "english": "today", "pos": "adverb", "category": "time"},
        {"greek": "αύριο", "english": "tomorrow", "pos": "adverb", "category": "time"},
        {"greek": "χθες", "english": "yesterday", "pos": "adverb", "category": "time"},
        {"greek": "εδώ", "english": "here", "pos": "adverb", "category": "place"},
        {"greek": "εκεί", "english": "there", "pos": "adverb", "category": "place"},
        {"greek": "μπροστά", "english": "in front/ahead", "pos": "adverb", "category": "place"},
        {"greek": "πίσω", "english": "behind/back", "pos": "adverb", "category": "place"},
        {"greek": "πάνω", "english": "up/above", "pos": "adverb", "category": "place"},
        {"greek": "κάτω", "english": "down/below", "pos": "adverb", "category": "place"},
        {"greek": "δεξιά", "english": "right (direction)", "pos": "adverb", "category": "place"},
        {"greek": "αριστερά", "english": "left (direction)", "pos": "adverb", "category": "place"},
        {"greek": "μαζί", "english": "together", "pos": "adverb", "category": "description"},
        {"greek": "μόνο", "english": "only", "pos": "adverb", "category": "description"},
        {"greek": "ίσως", "english": "maybe/perhaps", "pos": "adverb", "category": "description"},
        {"greek": "βέβαια", "english": "of course/certainly", "pos": "adverb", "category": "description"},
        {"greek": "επίσης", "english": "also/too", "pos": "adverb", "category": "description"},
        {"greek": "γρήγορα", "english": "quickly", "pos": "adverb", "category": "description"},
        {"greek": "αργά", "english": "slowly/late", "pos": "adverb", "category": "description"},

        # ===== Common verbs (general) =====
        {"greek": "είμαι", "english": "to be", "pos": "verb", "category": "general"},
        {"greek": "έχω", "english": "to have", "pos": "verb", "category": "general"},
        {"greek": "κάνω", "english": "to do/make", "pos": "verb", "category": "general"},
        {"greek": "πάω", "english": "to go", "pos": "verb", "category": "general"},
        {"greek": "έρχομαι", "english": "to come", "pos": "verb", "category": "general"},
        {"greek": "λέω", "english": "to say/tell", "pos": "verb", "category": "general"},
        {"greek": "μιλάω", "english": "to speak/talk", "pos": "verb", "category": "general"},
        {"greek": "ακούω", "english": "to hear/listen", "pos": "verb", "category": "general"},
        {"greek": "βλέπω", "english": "to see/watch", "pos": "verb", "category": "general"},
        {"greek": "ξέρω", "english": "to know", "pos": "verb", "category": "general"},
        {"greek": "θέλω", "english": "to want", "pos": "verb", "category": "general"},
        {"greek": "μπορώ", "english": "to be able/can", "pos": "verb", "category": "general"},
        {"greek": "πρέπει", "english": "must/should", "pos": "verb", "category": "general"},
        {"greek": "δίνω", "english": "to give", "pos": "verb", "category": "general"},
        {"greek": "παίρνω", "english": "to take/get", "pos": "verb", "category": "general"},
        {"greek": "βρίσκω", "english": "to find", "pos": "verb", "category": "general"},
        {"greek": "ψάχνω", "english": "to search/look for", "pos": "verb", "category": "general"},
        {"greek": "ζω", "english": "to live", "pos": "verb", "category": "general"},
        {"greek": "μένω", "english": "to stay/live", "pos": "verb", "category": "general"},
        {"greek": "ανοίγω", "english": "to open", "pos": "verb", "category": "general"},
        {"greek": "κλείνω", "english": "to close", "pos": "verb", "category": "general"},
        {"greek": "αρχίζω", "english": "to begin/start", "pos": "verb", "category": "general"},
        {"greek": "τελειώνω", "english": "to finish/end", "pos": "verb", "category": "general"},
        {"greek": "περιμένω", "english": "to wait", "pos": "verb", "category": "general"},
        {"greek": "βοηθάω", "english": "to help", "pos": "verb", "category": "general"},
        {"greek": "χρειάζομαι", "english": "to need", "pos": "verb", "category": "general"},
        {"greek": "αλλάζω", "english": "to change", "pos": "verb", "category": "general"},
        {"greek": "φέρνω", "english": "to bring", "pos": "verb", "category": "general"},
        {"greek": "σταματάω", "english": "to stop", "pos": "verb", "category": "general"},
        {"greek": "συνεχίζω", "english": "to continue", "pos": "verb", "category": "general"},
        {"greek": "προσπαθώ", "english": "to try", "pos": "verb", "category": "general"},
        {"greek": "καταλαβαίνω", "english": "to understand", "pos": "verb", "category": "general"},
        {"greek": "θυμάμαι", "english": "to remember", "pos": "verb", "category": "general"},
        {"greek": "ξεχνάω", "english": "to forget", "pos": "verb", "category": "general"},
        {"greek": "αποφασίζω", "english": "to decide", "pos": "verb", "category": "general"},
        {"greek": "εξηγώ", "english": "to explain", "pos": "verb", "category": "general"},
        {"greek": "ρωτάω", "english": "to ask", "pos": "verb", "category": "general"},
        {"greek": "απαντάω", "english": "to answer", "pos": "verb", "category": "general"},
        {"greek": "σκέφτομαι", "english": "to think", "pos": "verb", "category": "general"},
        {"greek": "αισθάνομαι", "english": "to feel", "pos": "verb", "category": "general"},

        # ===== Pronouns =====
        {"greek": "εγώ", "english": "I", "pos": "pronoun", "category": "grammar"},
        {"greek": "εσύ", "english": "you (singular)", "pos": "pronoun", "category": "grammar"},
        {"greek": "αυτός", "english": "he/this", "pos": "pronoun", "category": "grammar"},
        {"greek": "αυτή", "english": "she/this", "pos": "pronoun", "category": "grammar"},
        {"greek": "αυτό", "english": "it/this", "pos": "pronoun", "category": "grammar"},
        {"greek": "εμείς", "english": "we", "pos": "pronoun", "category": "grammar"},
        {"greek": "εσείς", "english": "you (plural/formal)", "pos": "pronoun", "category": "grammar"},
        {"greek": "αυτοί", "english": "they (masc)", "pos": "pronoun", "category": "grammar"},
        {"greek": "αυτές", "english": "they (fem)", "pos": "pronoun", "category": "grammar"},
        {"greek": "αυτά", "english": "they (neut)", "pos": "pronoun", "category": "grammar"},
        {"greek": "κάποιος", "english": "someone", "pos": "pronoun", "category": "grammar"},
        {"greek": "κανείς", "english": "nobody/anyone", "pos": "pronoun", "category": "grammar"},
        {"greek": "κάτι", "english": "something", "pos": "pronoun", "category": "grammar"},
        {"greek": "τίποτα", "english": "nothing/anything", "pos": "pronoun", "category": "grammar"},
        {"greek": "όλοι", "english": "everyone/all", "pos": "pronoun", "category": "grammar"},
        {"greek": "ο καθένας", "english": "each one", "pos": "pronoun", "category": "grammar"},

        # ===== Conjunctions =====
        {"greek": "και", "english": "and", "pos": "conjunction", "category": "grammar"},
        {"greek": "ή", "english": "or", "pos": "conjunction", "category": "grammar"},
        {"greek": "αλλά", "english": "but", "pos": "conjunction", "category": "grammar"},
        {"greek": "όμως", "english": "however", "pos": "conjunction", "category": "grammar"},
        {"greek": "γιατί", "english": "because/why", "pos": "conjunction", "category": "grammar"},
        {"greek": "επειδή", "english": "because/since", "pos": "conjunction", "category": "grammar"},
        {"greek": "αν", "english": "if", "pos": "conjunction", "category": "grammar"},
        {"greek": "ότι", "english": "that", "pos": "conjunction", "category": "grammar"},
        {"greek": "όταν", "english": "when", "pos": "conjunction", "category": "grammar"},
        {"greek": "ενώ", "english": "while/whereas", "pos": "conjunction", "category": "grammar"},
        {"greek": "αφού", "english": "since/after", "pos": "conjunction", "category": "grammar"},
        {"greek": "πριν", "english": "before", "pos": "conjunction", "category": "grammar"},
        {"greek": "μετά", "english": "after", "pos": "conjunction", "category": "grammar"},
        {"greek": "ώστε", "english": "so that", "pos": "conjunction", "category": "grammar"},
        {"greek": "ούτε", "english": "neither/nor", "pos": "conjunction", "category": "grammar"},

        # ===== Prepositions =====
        {"greek": "σε", "english": "in/at/to", "pos": "preposition", "category": "grammar"},
        {"greek": "από", "english": "from", "pos": "preposition", "category": "grammar"},
        {"greek": "με", "english": "with", "pos": "preposition", "category": "grammar"},
        {"greek": "για", "english": "for/about", "pos": "preposition", "category": "grammar"},
        {"greek": "χωρίς", "english": "without", "pos": "preposition", "category": "grammar"},
        {"greek": "μέχρι", "english": "until/up to", "pos": "preposition", "category": "grammar"},
        {"greek": "κατά", "english": "during/against", "pos": "preposition", "category": "grammar"},
        {"greek": "μεταξύ", "english": "between/among", "pos": "preposition", "category": "grammar"},
        {"greek": "προς", "english": "towards", "pos": "preposition", "category": "grammar"},
        {"greek": "εκτός", "english": "except/outside", "pos": "preposition", "category": "grammar"},

        # ===== Common phrases =====
        {"greek": "καλημέρα", "english": "good morning", "pos": "phrase", "category": "greetings"},
        {"greek": "καλησπέρα", "english": "good evening", "pos": "phrase", "category": "greetings"},
        {"greek": "καληνύχτα", "english": "good night", "pos": "phrase", "category": "greetings"},
        {"greek": "γεια σου", "english": "hello/goodbye (informal)", "pos": "phrase", "category": "greetings"},
        {"greek": "γεια σας", "english": "hello/goodbye (formal)", "pos": "phrase", "category": "greetings"},
        {"greek": "ευχαριστώ", "english": "thank you", "pos": "phrase", "category": "greetings"},
        {"greek": "παρακαλώ", "english": "please/you're welcome", "pos": "phrase", "category": "greetings"},
        {"greek": "συγγνώμη", "english": "sorry/excuse me", "pos": "phrase", "category": "greetings"},
        {"greek": "εντάξει", "english": "okay", "pos": "phrase", "category": "greetings"},
        {"greek": "βέβαια", "english": "of course", "pos": "phrase", "category": "greetings"},
        {"greek": "τι κάνεις;", "english": "how are you?", "pos": "phrase", "category": "greetings"},
        {"greek": "πώς σε λένε;", "english": "what is your name?", "pos": "phrase", "category": "greetings"},
        {"greek": "με λένε...", "english": "my name is...", "pos": "phrase", "category": "greetings"},
        {"greek": "δεν καταλαβαίνω", "english": "I don't understand", "pos": "phrase", "category": "greetings"},
        {"greek": "μιλάτε αγγλικά;", "english": "do you speak English?", "pos": "phrase", "category": "greetings"},

        # ===== Time-related nouns =====
        {"greek": "η ώρα", "english": "hour/time", "pos": "noun", "article": "η", "category": "time"},
        {"greek": "το λεπτό", "english": "minute", "pos": "noun", "article": "το", "category": "time"},
        {"greek": "το δευτερόλεπτο", "english": "second", "pos": "noun", "article": "το", "category": "time"},
        {"greek": "η μέρα", "english": "day", "pos": "noun", "article": "η", "category": "time"},
        {"greek": "η εβδομάδα", "english": "week", "pos": "noun", "article": "η", "category": "time"},
        {"greek": "ο μήνας", "english": "month", "pos": "noun", "article": "ο", "category": "time"},
        {"greek": "ο χρόνος", "english": "year/time", "pos": "noun", "article": "ο", "category": "time"},
        {"greek": "το πρωί", "english": "morning", "pos": "noun", "article": "το", "category": "time"},
        {"greek": "το μεσημέρι", "english": "noon", "pos": "noun", "article": "το", "category": "time"},
        {"greek": "το απόγευμα", "english": "afternoon", "pos": "noun", "article": "το", "category": "time"},
        {"greek": "το βράδυ", "english": "evening/night", "pos": "noun", "article": "το", "category": "time"},
        {"greek": "η Δευτέρα", "english": "Monday", "pos": "noun", "article": "η", "category": "time"},
        {"greek": "η Τρίτη", "english": "Tuesday", "pos": "noun", "article": "η", "category": "time"},
        {"greek": "η Τετάρτη", "english": "Wednesday", "pos": "noun", "article": "η", "category": "time"},
        {"greek": "η Πέμπτη", "english": "Thursday", "pos": "noun", "article": "η", "category": "time"},
        {"greek": "η Παρασκευή", "english": "Friday", "pos": "noun", "article": "η", "category": "time"},
        {"greek": "το Σάββατο", "english": "Saturday", "pos": "noun", "article": "το", "category": "time"},
        {"greek": "η Κυριακή", "english": "Sunday", "pos": "noun", "article": "η", "category": "time"},

        # ===== Numbers (as words) =====
        {"greek": "ένα", "english": "one", "pos": "adjective", "category": "numbers"},
        {"greek": "δύο", "english": "two", "pos": "adjective", "category": "numbers"},
        {"greek": "τρία", "english": "three", "pos": "adjective", "category": "numbers"},
        {"greek": "τέσσερα", "english": "four", "pos": "adjective", "category": "numbers"},
        {"greek": "πέντε", "english": "five", "pos": "adjective", "category": "numbers"},
        {"greek": "έξι", "english": "six", "pos": "adjective", "category": "numbers"},
        {"greek": "εφτά", "english": "seven", "pos": "adjective", "category": "numbers"},
        {"greek": "οχτώ", "english": "eight", "pos": "adjective", "category": "numbers"},
        {"greek": "εννιά", "english": "nine", "pos": "adjective", "category": "numbers"},
        {"greek": "δέκα", "english": "ten", "pos": "adjective", "category": "numbers"},
        {"greek": "είκοσι", "english": "twenty", "pos": "adjective", "category": "numbers"},
        {"greek": "τριάντα", "english": "thirty", "pos": "adjective", "category": "numbers"},
        {"greek": "σαράντα", "english": "forty", "pos": "adjective", "category": "numbers"},
        {"greek": "πενήντα", "english": "fifty", "pos": "adjective", "category": "numbers"},
        {"greek": "εκατό", "english": "hundred", "pos": "adjective", "category": "numbers"},
        {"greek": "χίλια", "english": "thousand", "pos": "adjective", "category": "numbers"},
        {"greek": "πρώτος", "english": "first", "pos": "adjective", "category": "numbers"},
        {"greek": "δεύτερος", "english": "second", "pos": "adjective", "category": "numbers"},
        {"greek": "τρίτος", "english": "third", "pos": "adjective", "category": "numbers"},
        {"greek": "τελευταίος", "english": "last", "pos": "adjective", "category": "numbers"},

        # ===== Colors =====
        {"greek": "κόκκινος", "english": "red", "pos": "adjective", "category": "colors"},
        {"greek": "μπλε", "english": "blue", "pos": "adjective", "category": "colors"},
        {"greek": "πράσινος", "english": "green", "pos": "adjective", "category": "colors"},
        {"greek": "κίτρινος", "english": "yellow", "pos": "adjective", "category": "colors"},
        {"greek": "μαύρος", "english": "black", "pos": "adjective", "category": "colors"},
        {"greek": "άσπρος", "english": "white", "pos": "adjective", "category": "colors"},
        {"greek": "γκρίζος", "english": "gray", "pos": "adjective", "category": "colors"},
        {"greek": "καφέ", "english": "brown", "pos": "adjective", "category": "colors"},
        {"greek": "ροζ", "english": "pink", "pos": "adjective", "category": "colors"},
        {"greek": "πορτοκαλί", "english": "orange (color)", "pos": "adjective", "category": "colors"},

        # ===== Clothing =====
        {"greek": "τα ρούχα", "english": "clothes", "pos": "noun", "article": "τα", "category": "clothing"},
        {"greek": "το παντελόνι", "english": "trousers/pants", "pos": "noun", "article": "το", "category": "clothing"},
        {"greek": "η φούστα", "english": "skirt", "pos": "noun", "article": "η", "category": "clothing"},
        {"greek": "το φόρεμα", "english": "dress", "pos": "noun", "article": "το", "category": "clothing"},
        {"greek": "το πουκάμισο", "english": "shirt", "pos": "noun", "article": "το", "category": "clothing"},
        {"greek": "η μπλούζα", "english": "blouse/top", "pos": "noun", "article": "η", "category": "clothing"},
        {"greek": "το μπουφάν", "english": "jacket", "pos": "noun", "article": "το", "category": "clothing"},
        {"greek": "το παλτό", "english": "coat", "pos": "noun", "article": "το", "category": "clothing"},
        {"greek": "τα παπούτσια", "english": "shoes", "pos": "noun", "article": "τα", "category": "clothing"},
        {"greek": "οι κάλτσες", "english": "socks", "pos": "noun", "article": "οι", "category": "clothing"},
        {"greek": "το καπέλο", "english": "hat", "pos": "noun", "article": "το", "category": "clothing"},
        {"greek": "η τσάντα", "english": "bag/purse", "pos": "noun", "article": "η", "category": "clothing"},

        # ===== City & places =====
        {"greek": "η πόλη", "english": "city", "pos": "noun", "article": "η", "category": "places"},
        {"greek": "το χωριό", "english": "village", "pos": "noun", "article": "το", "category": "places"},
        {"greek": "η πλατεία", "english": "square/plaza", "pos": "noun", "article": "η", "category": "places"},
        {"greek": "η γωνία", "english": "corner", "pos": "noun", "article": "η", "category": "places"},
        {"greek": "η εκκλησία", "english": "church", "pos": "noun", "article": "η", "category": "places"},
        {"greek": "το νοσοκομείο", "english": "hospital", "pos": "noun", "article": "το", "category": "places"},
        {"greek": "η τράπεζα", "english": "bank", "pos": "noun", "article": "η", "category": "places"},
        {"greek": "το ταχυδρομείο", "english": "post office", "pos": "noun", "article": "το", "category": "places"},
        {"greek": "η αστυνομία", "english": "police", "pos": "noun", "article": "η", "category": "places"},
        {"greek": "η πυροσβεστική", "english": "fire department", "pos": "noun", "article": "η", "category": "places"},
        {"greek": "το πάρκο", "english": "park", "pos": "noun", "article": "το", "category": "places"},
        {"greek": "το σινεμά", "english": "cinema", "pos": "noun", "article": "το", "category": "places"},
        {"greek": "το βενζινάδικο", "english": "gas station", "pos": "noun", "article": "το", "category": "places"},
    ]


# Articles for common noun endings (heuristic)
ARTICLE_RULES = {
    # Masculine endings -> ο
    "ος": "ο", "ής": "ο", "ας": "ο", "ές": "ο",
    # Feminine endings -> η
    "η": "η", "ά": "η", "α": "η", "ση": "η", "ξη": "η",
    # Neuter endings -> το
    "ο": "το", "ί": "το", "μα": "το", "ιο": "το",
}


def guess_article(greek_word: str) -> str | None:
    """Guess the article for a Greek noun based on ending."""
    word = greek_word.strip()
    # Try longest endings first
    for length in [2, 1]:
        ending = word[-length:] if len(word) >= length else ""
        if ending in ARTICLE_RULES:
            return ARTICLE_RULES[ending]
    return None


def classify_pos(greek: str, english: str) -> str:
    """Heuristic to classify part of speech from Greek/English text."""
    greek_lower = greek.lower().strip()
    english_lower = english.lower().strip()

    # Check if it starts with an article
    if greek_lower.startswith(("ο ", "η ", "το ", "οι ", "τα ", "τις ", "τους ", "των ")):
        return "noun"

    # Check English for verb indicators
    if english_lower.startswith("to "):
        return "verb"

    # Common Greek verb endings
    if greek_lower.endswith(("ω", "ώ", "ομαι", "άμαι", "ιέμαι", "ούμαι", "είμαι")):
        return "verb"

    # Adjective patterns
    if english_lower.endswith((" (adj)", "(adj)")):
        return "adjective"

    return "noun"  # default


def extract_article_from_greek(greek: str) -> tuple[str | None, str]:
    """Extract article from Greek word if present. Returns (article, clean_word)."""
    articles = ["ο ", "η ", "το ", "οι ", "τα ", "τις ", "τους "]
    greek_stripped = greek.strip()
    for art in articles:
        if greek_stripped.lower().startswith(art):
            return art.strip(), greek_stripped
    return None, greek_stripped


def compile_vocabulary():
    """Main function to compile all vocabulary sources into the database."""
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}. Run create_db.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Track existing words to avoid duplicates (normalized lowercase Greek)
    seen = set()
    total_inserted = 0

    def insert_word(greek: str, english: str, pos: str, article: str | None = None,
                    category: str | None = None, notes: str | None = None) -> bool:
        nonlocal total_inserted
        key = greek.lower().strip()
        if key in seen:
            return False
        seen.add(key)
        cursor.execute(
            "INSERT INTO words (greek, english, part_of_speech, article, category, notes) VALUES (?, ?, ?, ?, ?, ?)",
            (greek.strip(), english.strip(), pos, article, category, notes)
        )
        total_inserted += 1
        return True

    # 1. Load curated B1 vocabulary first (highest quality)
    print("Loading curated B1 vocabulary...")
    curated = get_curated_b1_vocabulary()
    curated_count = 0
    for entry in curated:
        article = entry.get("article")
        pos = entry.get("pos", "noun")
        # For nouns in curated list, the article is already in the greek text
        inserted = insert_word(
            entry["greek"], entry["english"], pos,
            article=article, category=entry.get("category")
        )
        if inserted:
            curated_count += 1
    print(f"  Inserted {curated_count} curated words")

    # 2. Load Duolingo vocab
    print("Loading Duolingo vocabulary...")
    try:
        duolingo_words = fetch_duolingo_vocab()
        duo_count = 0
        for entry in duolingo_words:
            greek = entry["greek"]
            english = entry["english"]
            pos = classify_pos(greek, english)
            article, clean_greek = extract_article_from_greek(greek)

            if pos == "noun" and article is None:
                article = guess_article(clean_greek)
                if article:
                    greek = f"{article} {clean_greek}"

            inserted = insert_word(greek, english, pos, article=article)
            if inserted:
                duo_count += 1
        print(f"  Inserted {duo_count} new words from Duolingo list")
    except Exception as e:
        print(f"  Warning: Could not fetch Duolingo vocab: {e}")

    conn.commit()

    # Post-processing: ensure all nouns have articles
    cursor.execute("SELECT id, greek FROM words WHERE part_of_speech = 'noun' AND article IS NULL")
    nouns_without_articles = cursor.fetchall()
    fixed = 0
    for word_id, greek in nouns_without_articles:
        article, clean = extract_article_from_greek(greek)
        if article is None:
            article = guess_article(clean)
        if article:
            cursor.execute("UPDATE words SET article = ?, greek = ? WHERE id = ?",
                           (article, f"{article} {clean}" if not greek.startswith(article) else greek, word_id))
            fixed += 1
    if fixed:
        print(f"  Fixed {fixed} nouns with missing articles")

    conn.commit()
    conn.close()

    print(f"\nTotal words inserted: {total_inserted}")
    print(f"Database saved to {DB_PATH}")


if __name__ == "__main__":
    compile_vocabulary()
