import os

from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv()

client = AsyncOpenAI(
    base_url=os.getenv("LLM_BASE_URL"),
    api_key=os.getenv("LLM_API_KEY", "not-needed")
)

MODEL = os.getenv("LLM_MODEL")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS"))
TEMPERATURE = float(os.getenv("LLM_TEMPERATURE"))

async def complete(prompt: str) -> str:
    response = await client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=MAX_TOKENS,
        temperature=TEMPERATURE
    )
    return response.choices[0].message.content.strip()