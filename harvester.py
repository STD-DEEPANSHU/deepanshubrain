# -*- coding: utf-8 -*-
"""
DeepanshuBrain - 24/7 Automated AI Brain Harvester
Harvests pure, authentic conversations from Baka Bot into NavyaBrain_DB.
"""

import asyncio
import time
import signal
import sys
from datetime import datetime
from pymongo import MongoClient, UpdateOne
import certifi

import config
from persona import clean_baka_reply, is_quality_dialogue, normalize_query
from prompt_streamer import PromptStreamer
from worker_pool import WorkerPool

is_running = True

def handle_sigint(sig, frame):
    global is_running
    print("\n🛑 Stop signal received. Finishing pending tasks and shutting down gracefully...")
    is_running = False

signal.signal(signal.SIGINT, handle_sigint)
signal.signal(signal.SIGTERM, handle_sigint)

async def main():
    global is_running
    print("=" * 65)
    print("🌸 DEEPANSHU BRAIN — AUTOMATED AI DIALOGUE HARVESTER 🌸")
    print("=" * 65)
    print(f"🎯 Target Bot: {config.TARGET_BOT}")
    print(f"💖 AI Persona Name: {config.BOT_NAME}")
    print(f"📦 Destination DB: {config.DEST_DB_NAME}")
    print(f"⏱️  Query Interval: ~{config.GLOBAL_QUERY_DELAY}s (Safe Round-Robin)")
    print("=" * 65 + "\n")

    # 1. Connect Destination MongoDB
    try:
        dest_client = MongoClient(
            config.DEST_MONGO_URL,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=8000
        )
        dest_db = dest_client[config.DEST_DB_NAME]
        train_col = dest_db["training_dataset"]
        brain_col = dest_db["learned_brain"]
        cfg_col = dest_db["bot_config"]
        print(f"✅ Connected to Destination DB: {config.DEST_DB_NAME}")
    except Exception as e:
        print(f"❌ Failed to connect to Destination MongoDB: {e}")
        return

    # 2. Fetch Active Worker Sessions
    cfg_doc = cfg_col.find_one({"type": "session_config"}) or {}
    sessions = cfg_doc.get("sessions", [])
    if not sessions:
        print("❌ No string sessions found in NavyaBrain_DB.bot_config!")
        return

    print(f"📋 Found {len(sessions)} configured worker sessions.")

    # 3. Initialize Worker Pool
    pool = WorkerPool(sessions)
    await pool.start_all()

    # 4. Initialize Prompt Streamer
    streamer = PromptStreamer(dest_db)

    # 5. Tracking Stats
    start_time = time.time()
    harvested_count = 0
    skipped_count = 0
    current_total_in_db = train_col.count_documents({})
    print(f"📊 Starting with {current_total_in_db:,} existing dialogues in {config.DEST_DB_NAME}.\n")
    print("🚀 Starting 24/7 Harvest Loop! Press Ctrl+C at any time to stop.\n")

    batch_offset = 0
    prompt_generator = streamer.stream_prompts(batch_size=5000, skip=batch_offset)

    while is_running:
        try:
            try:
                raw_prompt = next(prompt_generator)
            except StopIteration:
                batch_offset += 5000
                print(f"🔄 Streaming next 5,000 prompts (offset: {batch_offset:,})...")
                prompt_generator = streamer.stream_prompts(batch_size=5000, skip=batch_offset)
                raw_prompt = next(prompt_generator)

            # Check if this exact prompt was already learned in learned_brain
            q_clean = normalize_query(raw_prompt)
            if brain_col.find_one({"q_clean": q_clean}):
                skipped_count += 1
                continue

            # Pick next available round-robin worker
            worker = pool.get_next_worker()
            if not worker:
                await asyncio.sleep(1.0)
                continue

            # Query Baka Bot
            res = await worker.query(raw_prompt)
            if not res:
                skipped_count += 1
                await asyncio.sleep(config.GLOBAL_QUERY_DELAY)
                continue

            raw_reply = res.get("response", "")
            reactions = res.get("reactions", [])
            sticker = res.get("sticker")

            # Clean and filter reply
            clean_reply = clean_baka_reply(raw_reply, bot_name=config.BOT_NAME)

            if not is_quality_dialogue(raw_prompt, clean_reply):
                skipped_count += 1
                await asyncio.sleep(config.GLOBAL_QUERY_DELAY)
                continue

            # Save to MongoDB training_dataset
            now = datetime.utcnow()
            doc = {
                "source": "live_clone_chat",
                "category": "personal_dm",
                "prompt": raw_prompt,
                "response": clean_reply,
                "raw_baka_reply": raw_reply,
                "reactions": reactions,
                "sticker": sticker,
                "worker": worker.username,
                "created_at": now
            }
            train_col.insert_one(doc)

            # Sync to learned_brain
            brain_col.update_one(
                {"q_clean": q_clean},
                {"$set": {
                    "q_clean": q_clean,
                    "prompt": raw_prompt,
                    "response": clean_reply,
                    "reactions": reactions,
                    "category": "personal_dm",
                    "updated_at": now
                }},
                upsert=True
            )

            harvested_count += 1
            current_total_in_db += 1

            # Calculate live speed
            elapsed = time.time() - start_time
            rate_per_min = (harvested_count / elapsed) * 60 if elapsed > 0 else 0
            rate_per_hour = rate_per_min * 60

            # Pretty status log
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] "
                f"🎉 #{harvested_count:,} (Total: {current_total_in_db:,}) | "
                f"Speed: {rate_per_min:.1f}/min ({rate_per_hour:.0f}/hr) | "
                f"By: @{worker.username}\n"
                f"   User: \"{raw_prompt}\"\n"
                f"   🌸 {config.BOT_NAME}: \"{clean_reply}\" {reactions}\n"
            )

            # Global safety delay
            await asyncio.sleep(config.GLOBAL_QUERY_DELAY)

        except Exception as e:
            print(f"⚠️ Loop exception: {e}")
            await asyncio.sleep(3.0)

    # Graceful Shutdown
    await pool.stop_all()
    print("\n" + "=" * 65)
    print("🏁 HARVEST SESSION COMPLETED")
    print(f"✨ New Dialogues Collected: {harvested_count:,}")
    print(f"📦 Total in Database Now: {current_total_in_db:,}")
    print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
