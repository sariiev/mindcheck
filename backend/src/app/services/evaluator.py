import json
from pathlib import Path

from app.services.llm import complete

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def load_prompt(file_name: str) -> str:
    return (PROMPTS_DIR / file_name).read_text()

async def evaluate_answer(
        question: str,
        user_answer: str,
        reference_answer: str | None = None,
        strictness: int = 5
) -> tuple[float, str]:
    reference_section = (
        f"Reference answer: {reference_answer}"
        if reference_answer
        else "Reference answer: Not provided — evaluate based on your knowledge."
    )

    prompt = load_prompt("evaluate_answer.txt").format(
        question=question,
        reference_section=reference_section,
        user_answer=user_answer,
        strictness=strictness
    )

    content = await complete(prompt)

    try:
        data = json.loads(content)
        score = float(data["score"])
        score = max(0.0, min(100.0, score))
        feedback = data["feedback"]
    except (json.JSONDecodeError, KeyError, ValueError):
        score = 0.0
        feedback = content

    return score, feedback