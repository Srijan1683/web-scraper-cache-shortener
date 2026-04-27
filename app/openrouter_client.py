from app.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
from openai import OpenAI

api_key = OPENROUTER_API_KEY
if not api_key:
    raise ValueError("OPENROUTER_API_KEY not set")

model_name = OPENROUTER_MODEL

client = OpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=api_key,
)