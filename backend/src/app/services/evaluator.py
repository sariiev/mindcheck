import json
from pathlib import Path
from typing import TypedDict

from app.services.llm import complete

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def load_prompt(file_name: str) -> str:
    return (PROMPTS_DIR / file_name).read_text()

class EvaluationResult(TypedDict):
    score: float
    summary: str
    strengths: list[str]
    issues: list[str]
    suggestion: str

async def evaluate_answer(
        question: str,
        user_answer: str,
        reference_answer: str | None = None,
        strictness: int = 5
) -> EvaluationResult:
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
        score = float(data.get("score", 0))
        score = max(0.0, min(100.0, score))
        return {
            "score": score,
            "summary": data.get("summary", ""),
            "strengths": data.get("strengths", []),
            "issues": data.get("issues", []),
            "suggestion": data.get("suggestion", "")
        }
    except (json.JSONDecodeError, KeyError, ValueError):
        return {
            "score": 0.0,
            "summary": content,
            "strengths": [],
            "issues": [],
            "suggestion": ""
        }