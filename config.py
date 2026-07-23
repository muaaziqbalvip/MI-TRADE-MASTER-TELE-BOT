"""
MI Trade Master — Signal Bot Configuration
All tunables live here. Values are pulled from environment variables
(set as GitHub Actions secrets) with safe local defaults for testing.
"""
import os

# ---------------------------------------------------------------------------
# Telegram
# ---------------------------------------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ---------------------------------------------------------------------------
# Branding
# ---------------------------------------------------------------------------
BOT_NAME = "MI Trade Master"
BOT_TAGLINE = "Smart Money Signal Engine"

# ---------------------------------------------------------------------------
# Assets — merged from both legacy bots
# ---------------------------------------------------------------------------
ASSETS = {
    "forex_otc": [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURGBP",
        "EURJPY", "GBPJPY", "USDCHF", "NZDUSD", "EURCHF", "AUDCAD",
        "AUDCHF", "AUDJPY", "CADJPY", "CHFJPY", "EURAUD", "EURCAD",
        "GBPAUD", "GBPCAD", "GBPCHF", "NZDCAD", "NZDCHF", "NZDJPY",
    ],
    "forex_real": [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "EURGBP", "EURJPY", "GBPJPY", "USDCHF", "NZDUSD",
    ],
    "crypto": [
        "BTCUSDT", "ETHUSDT", "XRPUSDT", "LTCUSDT", "BNBUSDT",
        "ADAUSDT", "DOTUSDT", "LINKUSDT", "SOLUSDT", "DOGEUSDT",
    ],
    "commodities": [
        "XAUUSD", "XAGUSD", "USOIL", "NATGAS",
    ],
    "indices": [
        "US500", "US30", "USTEC", "UK100", "GER40", "JPN225",
    ],
}

# Maps our internal symbol -> data source + provider-specific symbol
# source: "binance" (crypto, live klines) or "yahoo" (forex/commodities/indices)
SYMBOL_MAP = {
    # Forex
    "EURUSD": {"source": "yahoo", "symbol": "EURUSD=X"},
    "GBPUSD": {"source": "yahoo", "symbol": "GBPUSD=X"},
    "USDJPY": {"source": "yahoo", "symbol": "USDJPY=X"},
    "AUDUSD": {"source": "yahoo", "symbol": "AUDUSD=X"},
    "USDCAD": {"source": "yahoo", "symbol": "USDCAD=X"},
    "EURGBP": {"source": "yahoo", "symbol": "EURGBP=X"},
    "EURJPY": {"source": "yahoo", "symbol": "EURJPY=X"},
    "GBPJPY": {"source": "yahoo", "symbol": "GBPJPY=X"},
    "USDCHF": {"source": "yahoo", "symbol": "USDCHF=X"},
    "NZDUSD": {"source": "yahoo", "symbol": "NZDUSD=X"},
    "EURCHF": {"source": "yahoo", "symbol": "EURCHF=X"},
    "AUDCAD": {"source": "yahoo", "symbol": "AUDCAD=X"},
    "AUDCHF": {"source": "yahoo", "symbol": "AUDCHF=X"},
    "AUDJPY": {"source": "yahoo", "symbol": "AUDJPY=X"},
    "CADJPY": {"source": "yahoo", "symbol": "CADJPY=X"},
    "CHFJPY": {"source": "yahoo", "symbol": "CHFJPY=X"},
    "EURAUD": {"source": "yahoo", "symbol": "EURAUD=X"},
    "EURCAD": {"source": "yahoo", "symbol": "EURCAD=X"},
    "GBPAUD": {"source": "yahoo", "symbol": "GBPAUD=X"},
    "GBPCAD": {"source": "yahoo", "symbol": "GBPCAD=X"},
    "GBPCHF": {"source": "yahoo", "symbol": "GBPCHF=X"},
    "NZDCAD": {"source": "yahoo", "symbol": "NZDCAD=X"},
    "NZDCHF": {"source": "yahoo", "symbol": "NZDCHF=X"},
    "NZDJPY": {"source": "yahoo", "symbol": "NZDJPY=X"},
    # Crypto (Binance)
    "BTCUSDT": {"source": "binance", "symbol": "BTCUSDT"},
    "ETHUSDT": {"source": "binance", "symbol": "ETHUSDT"},
    "XRPUSDT": {"source": "binance", "symbol": "XRPUSDT"},
    "LTCUSDT": {"source": "binance", "symbol": "LTCUSDT"},
    "BNBUSDT": {"source": "binance", "symbol": "BNBUSDT"},
    "ADAUSDT": {"source": "binance", "symbol": "ADAUSDT"},
    "DOTUSDT": {"source": "binance", "symbol": "DOTUSDT"},
    "LINKUSDT": {"source": "binance", "symbol": "LINKUSDT"},
    "SOLUSDT": {"source": "binance", "symbol": "SOLUSDT"},
    "DOGEUSDT": {"source": "binance", "symbol": "DOGEUSDT"},
    # Commodities / Indices (Yahoo futures/indices)
    "XAUUSD": {"source": "yahoo", "symbol": "GC=F"},
    "XAGUSD": {"source": "yahoo", "symbol": "SI=F"},
    "USOIL": {"source": "yahoo", "symbol": "CL=F"},
    "NATGAS": {"source": "yahoo", "symbol": "NG=F"},
    "US500": {"source": "yahoo", "symbol": "^GSPC"},
    "US30": {"source": "yahoo", "symbol": "^DJI"},
    "USTEC": {"source": "yahoo", "symbol": "^IXIC"},
    "UK100": {"source": "yahoo", "symbol": "^FTSE"},
    "GER40": {"source": "yahoo", "symbol": "^GDAXI"},
    "JPN225": {"source": "yahoo", "symbol": "^N225"},
}

DISPLAY_NAMES = {
    "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY",
    "AUDUSD": "AUD/USD", "USDCAD": "USD/CAD", "EURGBP": "EUR/GBP",
    "EURJPY": "EUR/JPY", "GBPJPY": "GBP/JPY", "USDCHF": "USD/CHF",
    "NZDUSD": "NZD/USD", "EURCHF": "EUR/CHF", "AUDCAD": "AUD/CAD",
    "AUDCHF": "AUD/CHF", "AUDJPY": "AUD/JPY", "CADJPY": "CAD/JPY",
    "CHFJPY": "CHF/JPY", "EURAUD": "EUR/AUD", "EURCAD": "EUR/CAD",
    "GBPAUD": "GBP/AUD", "GBPCAD": "GBP/CAD", "GBPCHF": "GBP/CHF",
    "NZDCAD": "NZD/CAD", "NZDCHF": "NZD/CHF", "NZDJPY": "NZD/JPY",
    "BTCUSDT": "Bitcoin", "ETHUSDT": "Ethereum", "XRPUSDT": "Ripple",
    "LTCUSDT": "Litecoin", "BNBUSDT": "BNB", "ADAUSDT": "Cardano",
    "DOTUSDT": "Polkadot", "LINKUSDT": "Chainlink", "SOLUSDT": "Solana",
    "DOGEUSDT": "Dogecoin",
    "XAUUSD": "Gold", "XAGUSD": "Silver", "USOIL": "Crude Oil",
    "NATGAS": "Natural Gas",
    "US500": "US 500", "US30": "US 30", "USTEC": "US Tech 100",
    "UK100": "UK 100", "GER40": "Germany 40", "JPN225": "Japan 225",
}

# ---------------------------------------------------------------------------
# Signal engine
# ---------------------------------------------------------------------------
TIMEFRAME = "1m"
CANDLE_LIMIT = 150
CONFIDENCE_THRESHOLD = 82.0       # minimum confidence to broadcast a signal
SIGNAL_SCAN_INTERVAL = 60         # seconds between scan cycles
MAX_SIGNALS_PER_CYCLE = 4         # avoid spamming subscribers

# ---------------------------------------------------------------------------
# Persistence (flat JSON files committed back to the repo by the workflow)
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
SUBSCRIBERS_FILE = os.path.join(DATA_DIR, "subscribers.json")
STATS_FILE = os.path.join(DATA_DIR, "stats.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "user_settings.json")

# ---------------------------------------------------------------------------
# Runtime (used by the self-restarting GitHub Actions loop)
# ---------------------------------------------------------------------------
MAX_RUNTIME_MINUTES = int(os.environ.get("MAX_RUNTIME_MINUTES", "340"))  # ~5h40m safety margin under the 6h job cap
ADMIN_CHAT_IDS = [x for x in os.environ.get("ADMIN_CHAT_IDS", "").split(",") if x]
