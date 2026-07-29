"""
ai/llm_client.py

Thin wrapper around the Groq API (OpenAI-compatible format). This file
only knows HOW to talk to the API (auth, sending a prompt, getting text
back). It knows NOTHING about SQL generation or insight writing --
that logic lives in prompts.py / generate_sql.py / generate_insights.py.

Keeping this separation means if you ever swap providers again,
you only touch this one file.
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. Add it to your .env file "
        "(see .env.example)."
    )

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url="https://api.groq.com/openai/v1",
)


def ask_llm(prompt: str, temperature: float = 0.2) -> str:
    """
    Sends `prompt` to the LLM and returns the plain text response.

    Kept the name ask_llm so the rest of the codebase
    (generate_sql.py, generate_insights.py) doesn't need to change.

    temperature is kept low (0.2) by default because for SQL
    generation we want consistent, predictable output -- not
    creative variation.
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content.strip()
