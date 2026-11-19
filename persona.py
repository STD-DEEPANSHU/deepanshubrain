# -*- coding: utf-8 -*-
"""
Persona Cleaning & Reply Normalization for DeepanshuBrain
Ensures harvested replies match Navya's sweet, cute, attitude girlfriend style.
"""

import re

# Common Telugu phrases that Baka occasionally outputs, to be converted or filtered
TELUGU_TRANSLATIONS = {
    r"\bnenu bagunnanu\b": "main badiya hu",
    r"\bnuvvu ela unnav\b": "tum kaise ho",
    r"\bela unnav\b": "kaise ho",
    r"\bemaindi cheppu\b": "kya hua batao",
    r"\bem sangathalu\b": "kya haal chal",
    r"\bmalli hello\b": "phir se hello",
    r"\bem cheppali\b": "kya kehna hai",
    r"\banukuntunnav\b": "chahte ho"
}

def clean_baka_reply(text: str, bot_name: str = "Navya") -> str:
    """
    Cleans raw Baka replies:
    1. Replaces Baka / bakabot with the custom persona bot_name.
    2. Translates common Telugu artifacts into natural Hinglish.
    3. Normalizes whitespace and trailing links/tags.
    """
    if not text or not isinstance(text, str):
        return ""

    cleaned = text.strip()

    # 1. Replace Baka name variants
    cleaned = re.sub(r"@im_bakabot", f"@{bot_name.lower()}bot", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"@bakabot", f"@{bot_name.lower()}bot", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bbaka bot\b", f"{bot_name} bot", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bbakabot\b", f"{bot_name}bot", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bbaka\b", bot_name, cleaned, flags=re.IGNORECASE)

    # 2. Translate Telugu fragments into Hinglish
    for pat, rep in TELUGU_TRANSLATIONS.items():
        cleaned = re.sub(pat, rep, cleaned, flags=re.IGNORECASE)

    # 3. Strip Telegram promotion links or bot handles at end
    cleaned = re.sub(r"https?://t\.me/\S+", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned

def is_quality_dialogue(prompt: str, response: str) -> bool:
    """
    Verifies that a dialogue pair is high-quality for AI training:
    - Non-empty and reasonable length.
    - Not a technical error message.
    - Has actual textual content.
    """
    if not prompt or not response:
        return False

    p = prompt.strip()
    r = response.strip()

    if len(p) < 2 or len(r) < 2:
        return False

    # Filter out system errors
    bad_phrases = [
        "an error occurred",
        "please try again",
        "rate limit",
        "bot is restarting",
        "service unavailable"
    ]
    if any(bp in r.lower() for bp in bad_phrases):
        return False

    # Ensure response has Hindi, English or Devanagari characters
    has_text = bool(re.search(r'[a-zA-Z\u0900-\u097F]', r))
    if not has_text:
        return False

    # Reject foreign scripts (Burmese, Arabic, Chinese)
    has_foreign = bool(re.search(r'[\u1000-\u109F\u0600-\u06FF\u4E00-\u9FFF]', r))
    if has_foreign:
        return False

    return True

def normalize_query(query: str) -> str:
    """Normalizes query for deduplication and indexing."""
    q = query.lower().strip()
    q = re.sub(r"[^\w\s]", "", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q
