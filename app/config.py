from __future__ import annotations
import os
from dotenv import load_dotenv

APP_TITLE = "Web Scraper API"
APP_VERSION = "1.0.0"

DEFAULT_TIMEOUT = 10
DEFAULT_CODE_LENGTH = 6
DIRECT_SUMMARY_TOKEN_LIMIT = 6000
CHUNK_TOKEN_LIMIT = 2500
OPENROUTER_HTTP_REFERER = "https://localhost:8000"

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini").strip()
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
