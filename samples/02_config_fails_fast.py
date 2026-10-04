"""Configuration that refuses to start rather than running half configured.

A service that boots with an empty API key fails later, in a request, with a
confusing error. Requiring the values at import time moves that failure to
startup where it belongs.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is not set")
    return value


VENDOR_BASE_URL = os.getenv("VENDOR_BASE_URL", "https://api.example.com")
VENDOR_API_KEY = require_env("VENDOR_API_KEY")
PHONE_NUMBER_ID = require_env("PHONE_NUMBER_ID")

# Optional: shared secret checked on inbound GPT Action requests.
GPT_SHARED_SECRET = os.getenv("GPT_SHARED_SECRET", "")

DATABASE_PATH = os.getenv("DATABASE_PATH") or "summary.db"
MAX_CONVERSATIONS = int(os.getenv("MAX_CONVERSATIONS", "25"))
HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))
