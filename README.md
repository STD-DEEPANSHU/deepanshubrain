# 🌸 DeepanshuBrain — 24/7 Multi-Worker AI Brain Harvester

High-speed, automated data harvesting engine designed to build a world-class Indian AI Girlfriend model by harvesting and learning from authentic interactions with `@im_bakabot`.

---

## 🌟 Key Features

- **2.9M+ Real Indian Questions Pool:** Streams natural, authentic Indian questions from MongoDB (`Word.WordDb`).
- **Multi-Worker Round-Robin:** Rotates 4+ human Telegram accounts with per-account safety cooldowns, eliminating rate limits and flood waits.
- **Full Multimodal Capture:** Automatically records Baka's text response, custom stickers, and emoji reactions (`🙈✨`, `🌸✨`, `🌚`).
- **Smart Persona Filter:** Replaces Baka names with custom girlfriend persona (`Navya`), cleans Telugu fragments, and drops spam/errors.
- **Dual-Database Sync:**
  - Saves full audit records in `training_dataset` for model fine-tuning.
  - Syncs directly into `learned_brain` for instant retrieval.
- **Deploy Anywhere:** Ready to run locally, on a VPS, Docker, Koyeb, Render, or Heroku.

---

## 🚀 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/STD-DEEPANSHU/deepanshubrain.git
cd deepanshubrain
pip install -r requirements.txt
```

### 2. Run Harvester
```bash
python harvester.py
```

---

## ⚙️ Configuration (`config.py`)

| Parameter | Default | Description |
| :--- | :--- | :--- |
| `TARGET_BOT` | `@im_bakabot` | Telegram bot to harvest from |
| `BOT_NAME` | `Navya` | AI girlfriend persona name |
| `GLOBAL_QUERY_DELAY` | `2.5` | Delay between consecutive queries |
| `PER_WORKER_COOLDOWN`| `10.0` | Minimum rest time per worker account |
| `DEST_DB_NAME` | `NavyaBrain_DB` | Destination MongoDB database |

---

## ☁️ 24/7 Cloud Deployment

### Docker
```bash
docker build -t deepanshubrain .
docker run -d --name deepanshu_harvester deepanshubrain
```

### Heroku / Koyeb
Simply link this GitHub repository and select the `worker` process (`python harvester.py`).
