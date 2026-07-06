import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Question, Answer, Project
from app.db.session import get_session
from app.services.evaluator import evaluate_answer

router = APIRouter(prefix="/questions/{question_id}/answers", tags=["answers"])

class AnswerCreate(BaseModel):
    text: str = Field(max_length=5000)
    strictness: int | None = Field(default=None, ge=1, le=10)

class AnswerResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    text: str
    score: float | None
    summary: str | None
    strengths: list[str]
    issues: list[str]
    suggestion: str | None
    answered_at: datetime
    strictness: int

    model_config = {"from_attributes": True}

@router.post("/", response_model=AnswerResponse)
async def submit_answer(
        question_id: uuid.UUID,
        data: AnswerCreate,
        session: AsyncSession = Depends(get_session)
):
    question = await session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    project = await session.get(Project, question.project_id)

    strictness = data.strictness if data.strictness is not None else project.strictness
    evaluation_result = await evaluate_answer(
        question=question.text,
        user_answer=data.text,
        reference_answer=question.reference_answer,
        strictness=strictness
    )

    answer = Answer(
        question_id=question_id,
        text=data.text,
        score=evaluation_result["score"],
        summary=evaluation_result["summary"],
        strengths=evaluation_result["strengths"],
        issues=evaluation_result["issues"],
        suggestion=evaluation_result["suggestion"],
        strictness=strictness
    )
    session.add(answer)
    await session.commit()
    await session.refresh(answer)
    return answer

@router.get("/", response_model=list[AnswerResponse])
async def get_answers(
        question_id: uuid.UUID,
        session: AsyncSession = Depends(get_session)
):
    answers = await session.execute(
        select(Answer)
        .where(Answer.question_id == question_id)
        .order_by(Answer.answered_at.desc())
    )
    return answers.scalars().all()