# -*- coding: utf-8 -*-
"""
Multi-Account Worker Pool for DeepanshuBrain
Rotates requests through verified human userbot accounts.
Ensures zero rate-limit bans by enforcing per-account cooldowns.
"""

import asyncio
import time
from pyrogram import Client
from pyrogram.errors import FloodWait, RPCError
import config

class HarvestWorker:
    def __init__(self, index: int, session_string: str):
        self.index = index
        self.session_string = session_string.strip()
        self.client: Client | None = None
        self.lock = asyncio.Lock()
        self.last_used: float = 0
        self.username: str = ""
        self.first_name: str = ""
        self.user_id: int = 0
        self.is_ready: bool = False

    async def start(self):
        try:
            self.client = Client(
                f"harvester_worker_{self.index}",
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=self.session_string,
                no_updates=True,
                in_memory=True
            )
            await self.client.start()
            me = await self.client.get_me()
            self.first_name = me.first_name or f"Worker #{self.index + 1}"
            self.username = me.username or str(me.id)
            self.user_id = me.id
            self.is_ready = True
            print(f"🟢 [Worker #{self.index + 1}] Connected as {self.first_name} (@{self.username})")
        except Exception as e:
            print(f"🔴 [Worker #{self.index + 1}] Failed to start: {e}")
            self.is_ready = False

    async def stop(self):
        if self.client:
            try:
                await self.client.stop()
            except Exception:
                pass
            self.is_ready = False

    async def query(self, prompt: str) -> dict | None:
        """
        Sends query to TARGET_BOT and awaits response.
        Captures: text, sticker, and emoji reactions.
        """
        if not self.is_ready or not self.client:
            return None

        async with self.lock:
            # Enforce per-worker cooldown
            now = time.time()
            elapsed = now - self.last_used
            if elapsed < config.PER_WORKER_COOLDOWN:
                await asyncio.sleep(config.PER_WORKER_COOLDOWN - elapsed)

            try:
                sent = await self.client.send_message(config.TARGET_BOT, prompt)
                self.last_used = time.time()
                
                # Wait for reply
                reply_text = None
                reactions = []
                sticker = None
                
                start_wait = time.time()
                while time.time() - start_wait < config.REPLY_TIMEOUT:
                    await asyncio.sleep(1.0)
                    async for m in self.client.get_chat_history(config.TARGET_BOT, limit=5):
                        if m.id > sent.id and not m.from_user.is_self:
                            reply_text = m.text or m.caption
                            if m.sticker:
                                sticker = m.sticker.emoji or m.sticker.file_id
                            if m.reactions and m.reactions.reactions:
                                reactions = [r.emoji for r in m.reactions.reactions if getattr(r, 'emoji', None)]
                            break
                    if reply_text or sticker:
                        break

                if not reply_text and not sticker:
                    return None

                return {
                    "prompt": prompt,
                    "response": reply_text or (f"[Sticker: {sticker}]" if sticker else ""),
                    "reactions": reactions,
                    "sticker": sticker,
                    "worker_name": self.first_name,
                    "worker_user": self.username
                }
            except FloodWait as fw:
                print(f"⏳ [Worker #{self.index + 1}] FloodWait {fw.value}s. Sleeping worker...")
                self.last_used = time.time() + fw.value
                return None
            except RPCError as rpc:
                print(f"⚠️ [Worker #{self.index + 1}] Telegram RPC Error: {rpc}")
                return None
            except Exception as e:
                print(f"⚠️ [Worker #{self.index + 1}] Query error: {e}")
                return None

class WorkerPool:
    def __init__(self, sessions: list[str]):
        self.workers = [HarvestWorker(i, s) for i, s in enumerate(sessions)]
        self.current_idx = 0

    async def start_all(self):
        print(f"🚀 Initializing {len(self.workers)} accounts in Worker Pool...")
        await asyncio.gather(*(w.start() for w in self.workers))
        active = sum(1 for w in self.workers if w.is_ready)
        print(f"✅ {active} of {len(self.workers)} Workers are READY to harvest!\n")

    async def stop_all(self):
        await asyncio.gather(*(w.stop() for w in self.workers))

    def get_next_worker(self) -> HarvestWorker | None:
        """Round-robin selection of the next available ready worker."""
        ready_workers = [w for w in self.workers if w.is_ready]
        if not ready_workers:
            return None

        # Select worker that has been idle the longest
        now = time.time()
        ready_workers.sort(key=lambda w: w.last_used)
        return ready_workers[0]
