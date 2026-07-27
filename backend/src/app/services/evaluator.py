import json
import re
from pathlib import Path
from typing import TypedDict

from app.services.llm import complete
from app.services.vector_store import search_chunks

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

def load_prompt(file_name: str) -> str:
    return (PROMPTS_DIR / file_name).read_text()

class EvaluationResult(TypedDict):
    score: float
    summary: str
    strengths: list[str]
    issues: list[str]
    suggestion: str

def extract_json(content: str) -> dict:
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        return json.loads(match.group())
    raise json.JSONDecodeError("No JSON found", content, 0)

async def evaluate_answer(
        question: str,
        user_answer: str,
        reference_answer: str | None = None,
        strictness: int = 5,
        project_id: str | None = None
) -> EvaluationResult:
    reference_section = (
        f"Reference answer: {reference_answer}"
        if reference_answer
        else "Reference answer: Not provided — evaluate based on your knowledge."
    )

    context = ""
    if project_id:
        chunks = search_chunks(project_id, question)
        if chunks:
            context = "\n\n".join(chunks)
            print(f"Found chunks: {context}")
        else:
            print("No chunks found")

    context_section = (
        f"""
        Use the following course material as the primary source for evaluation. 
        Prioritize this material over your general knowledge when assessing correctness:
        
        {context}
        """
    )

    prompt = load_prompt("evaluate_answer.txt").format(
        question=question,
        reference_section=reference_section,
        context_section=context_section,
        user_answer=user_answer,
        strictness=strictness
    )

    content = await complete(prompt)

    try:
        data = extract_json(content)
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