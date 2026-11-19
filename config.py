# -*- coding: utf-8 -*-
"""
DeepanshuBrain Configuration
Connects:
1. Destination MongoDB (where cleaned training pairs & worker sessions are stored)
2. Source Questions MongoDB (VIPBOY with 29 Lakh real user prompts)
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Credentials
API_ID = int(os.getenv("API_ID", "6435225"))
API_HASH = os.getenv("API_HASH", "4e984ea35f854762dcde906dce426c2d")

# Target Bot to Harvest from
TARGET_BOT = os.getenv("TARGET_BOT", "@im_bakabot")

# AI Personality Name (Replaces 'Baka' in answers)
BOT_NAME = os.getenv("BOT_NAME", "Navya")

# Destination Database (NavyaBrain_DB)
DEST_MONGO_URL = os.getenv(
    "DEST_MONGO_URL",
    "mongodb+srv://stdstorage:deep@cluster0.hq1jbmf.mongodb.net/?appName=Cluster0"
)
DEST_DB_NAME = os.getenv("DEST_DB_NAME", "NavyaBrain_DB")

# Source Questions Database (VIPBOY with 2.9M Indian Questions)
QUESTIONS_MONGO_URL = os.getenv(
    "QUESTIONS_MONGO_URL",
    "mongodb+srv://chatbotreply:storage@cluster0.3jijmf6.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)
QUESTIONS_DB_NAME = os.getenv("QUESTIONS_DB_NAME", "Anonymous")
QUESTIONS_COL_NAME = os.getenv("QUESTIONS_COL_NAME", "Word.WordDb")

# Rate Limiting & Safety Timers (in seconds)
GLOBAL_QUERY_DELAY = float(os.getenv("GLOBAL_QUERY_DELAY", "2.5"))   # Delay between any queries
PER_WORKER_COOLDOWN = float(os.getenv("PER_WORKER_COOLDOWN", "10.0")) # Minimum rest time for one account
REPLY_TIMEOUT = int(os.getenv("REPLY_TIMEOUT", "10"))                # Max wait for Baka response
