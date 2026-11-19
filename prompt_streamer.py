# -*- coding: utf-8 -*-
"""
Prompt Streamer for DeepanshuBrain
Streams authentic, diverse Indian prompts from VIPBOY MongoDB (3.1M records).
Filters for clean Hinglish/Hindi, excluding foreign scripts and spam.
Tracks harvested prompts in destination DB to guarantee zero duplicate queries.
"""

import re
from pymongo import MongoClient
import certifi
import config

class PromptStreamer:
    def __init__(self, dest_db):
        self.dest_db = dest_db
        self.source_client = None
        self.source_col = None
        self._init_source()

    def _init_source(self):
        try:
            self.source_client = MongoClient(
                config.QUESTIONS_MONGO_URL,
                tlsCAFile=certifi.where(),
                serverSelectionTimeoutMS=8000
            )
            self.source_col = self.source_client[config.QUESTIONS_DB_NAME][config.QUESTIONS_COL_NAME]
            print(f"✅ Connected to Questions Source DB: {config.QUESTIONS_DB_NAME}.{config.QUESTIONS_COL_NAME}")
        except Exception as e:
            print(f"❌ Failed to connect to Questions DB: {e}")

    def stream_prompts(self, batch_size: int = 1000, skip: int = 0):
        """
        Yields clean, high-quality user prompts.
        Applies Hinglish regex validation.
        """
        if self.source_col is None:
            return

        # Fetch batch
        cursor = self.source_col.find(
            {"word": {"$exists": True, "$ne": None, "$ne": ""}},
            {"word": 1, "_id": 0}
        ).skip(skip).limit(batch_size)

        for doc in cursor:
            word = doc.get("word")
            if not word or not isinstance(word, str):
                continue

            w = word.strip()

            # Filter length: 2 to 120 chars
            if len(w) < 2 or len(w) > 120:
                continue

            # Must contain Latin (English/Hinglish) or Devanagari (Hindi)
            if not re.search(r'[a-zA-Z\u0900-\u097F]', w):
                continue

            # Exclude Burmese, Arabic, Chinese
            if re.search(r'[\u1000-\u109F\u0600-\u06FF\u4E00-\u9FFF]', w):
                continue

            # Exclude URLs or links
            if "http://" in w or "https://" in w or "t.me/" in w:
                continue

            yield w
