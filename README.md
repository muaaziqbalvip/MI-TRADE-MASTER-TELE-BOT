# 🤖 MI Trade Master — Telegram Signal Bot

A pro-level, 24/7 Telegram trading signal bot combining **Smart Money Concepts
(SMC/ICT)** market-structure analysis with a **multi-indicator confluence
engine** (RSI, EMA stack, MACD, Bollinger Bands, Stochastic).

Merges and upgrades two earlier bots:
- **SR-Trader** — SMC/ICT structure analysis, Yahoo Finance forex/OTC data
- **Trade-main** — Binance crypto feed, RSI/EMA/MACD confidence scoring

Runs **entirely free, 24/7, on GitHub Actions** — no server required.

---

## ✨ Features

- 🧠 **Smart signal engine** — market structure (BOS/HH-HL/LH-LL) fused with
  5 technical indicators for high-confidence confluence scoring
- 📡 **Multi-market coverage** — Forex OTC, Forex Real, Crypto (Binance),
  Commodities, Indices
- 🎨 **Beautiful Telegram UI** — inline buttons, emoji-rich formatted signal
  cards, visual confidence bars, live navigation menus
- 📸 **Screenshot chart analysis (Vision AI)** — send any chart screenshot
  (Quotex, TradingView, MetaTrader, any platform) and get an instant
  AI-powered read of the visible price action, rendered back as a clean
  branded signal chart — no login or account access required, ever
- 🩺 **Live diagnostics** — `/logs` shows recent bot activity/errors right
  in Telegram, and specific error messages (missing API key, auth failure,
  rate limit, etc.) instead of one generic "something went wrong"
- ⚙️ **Per-user preferences** — subscribe/unsubscribe, pick asset categories,
  set your own minimum confidence threshold, and set your default chart
  timeframe + trade expiry for screenshot analysis
- 🎯 **On-demand signals** — tap any asset for an instant live analysis
- 📊 **Live stats dashboard** — total signals, win-direction split, top assets
- ♻️ **True 24/7 uptime** — self-restarting GitHub Actions workflow chains
  a new run before the previous one's runtime cap, with a 15-minute cron
  safety net in case the chain ever breaks
- 💾 **Zero-database persistence** — subscriber list, settings, and stats
  are stored as JSON and committed back to the repo automatically
- 🖼 **Auto-applied bot identity** — profile photo, name, and description
  are set programmatically on startup via Telegram's Bot API (no manual
  BotFather steps needed)
- 🔁 **Resilient data fetching** — Yahoo Finance symbols (gold, silver,
  oil, indices, OTC pairs) automatically fall back through multiple
  interval/period combinations if the tightest resolution has no data,
  instead of failing outright

---

## 🎨 A note on "colorful backgrounds"

Telegram's Bot API has **no way to set a per-message background color** —
chat wallpaper is a personal setting each user controls in their own app,
and bots cannot touch it. This is a Telegram platform limit, not a
limitation of this bot. What *is* achievable — and what this bot does —
is rich colored-block visual formatting (🟩/🟥 direction bars, colored
strip headers, confidence meters) plus a properly branded bot profile
photo/name/description, which is the closest thing to a "colorful pro
look" within what Telegram actually allows.

---

## 🚀 Setup (5 minutes)

### 1. Create your bot
Message [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` →
copy the token it gives you.

### 2. Push this repo to GitHub
Create a new **public or private** repository and push all these files to it.

### 3. Add your bot token as a secret
In your repo: **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `BOT_TOKEN` | The token from BotFather |
| `GROQ_API_KEY` | Free API key from [console.groq.com](https://console.groq.com) — powers screenshot chart analysis |
| `ADMIN_CHAT_IDS` | *(optional)* comma-separated Telegram chat IDs for admin alerts |

> 🔒 **Security note:** This bot never asks for, stores, or uses any trading
> platform login, password, or verification code. Screenshot analysis works
> purely by reading the image visually via AI vision — your account
> credentials are never touched, requested, or required.

### 4. Enable Actions & start the bot
Go to the **Actions** tab → select **"MI Trade Master — 24/7 Signal Bot"** →
**Run workflow**. That's it — it will now keep itself running forever,
automatically restarting before each 6-hour GitHub Actions job limit.

### 5. Talk to your bot
Open Telegram, find your bot, send `/start`. 🎉

---

## 🗂 Project Structure

```
mi-trade-master/
├── main.py              # Entry point — runs bot + scanner threads
├── bot.py                # Telegram handlers (commands, buttons)
├── scanner.py             # Background auto-scan + broadcast loop
├── engine.py               # Signal generation (SMC + confluence scoring)
├── vision.py                # Groq Vision AI — analyzes chart screenshots
├── chartgen.py                # Renders branded signal chart images
├── indicators.py            # RSI, EMA, MACD, Bollinger, Stochastic, structure
├── fetcher.py               # Binance + Yahoo Finance data fetching
├── ui.py                    # Message formatting & inline keyboards
├── storage.py                # JSON persistence (subscribers/settings/stats)
├── diagnostics.py             # Live log buffer + /logs command + admin alerts
├── branding.py                # Auto-sets bot photo/name/description on startup
├── config.py                   # All settings & asset symbol maps
├── data/                        # Persisted JSON state (auto-committed)
├── assets/
│   └── bot_icon.jpg               # Bot profile photo (auto-applied)
├── requirements.txt
└── .github/workflows/
    └── mi-trade-master.yml      # 24/7 self-restarting workflow
```

---

## 🩺 Troubleshooting

If screenshot analysis (or anything else) isn't working:

1. **Check ⚙️ Preferences → About → 🩺 System Health** in the bot — shows
   whether `BOT_TOKEN` and `GROQ_API_KEY` are actually configured.
2. **Send `/logs`** to the bot — shows the last 30 events (info/warnings/
   errors) from the current session, including the *specific* reason any
   screenshot analysis failed (missing key, invalid key, rate limit,
   network issue, etc.) instead of a generic error.
3. **Check the GitHub Actions run logs** (Actions tab → latest run →
   expand "Run MI Trade Master") for the full server-side log, including
   every fetch/analysis attempt.
4. If `/logs` says `no_api_key` or `auth_failed`, the `GROQ_API_KEY`
   secret is missing or wrong — add/fix it in **Settings → Secrets and
   variables → Actions**, then re-run the workflow.
5. If `/logs` says `parse_error`, the error detail now shows the model's
   actual raw output (not just a generic message) — the full response is
   also logged server-side in the GitHub Actions run for deeper debugging.
   The bot forces Groq's JSON mode (`response_format: json_object`) and
   automatically retries without it if a model rejects that parameter,
   so this should be rare.

If `ADMIN_CHAT_IDS` is set, `/logs` is restricted to those chat IDs, and
critical config errors (missing/invalid Groq key) are pushed to them
automatically the moment they happen.

---

## ⚙️ Configuration

Tweak `config.py` to adjust:
- `CONFIDENCE_THRESHOLD` — default minimum confidence for the auto-scanner
- `SIGNAL_SCAN_INTERVAL` — seconds between scan cycles (default 60)
- `MAX_SIGNALS_PER_CYCLE` — cap on broadcasts per cycle (avoids spam)
- `ASSETS` — add/remove symbols per category
- `SYMBOL_MAP` — map any new symbol to its Binance/Yahoo source ticker

---

## ⚠️ Disclaimer

This bot is for **educational purposes only**. Trading (especially binary
options / OTC) carries significant financial risk. Signals are generated
algorithmically and are **not financial advice**. Always manage your own risk.
