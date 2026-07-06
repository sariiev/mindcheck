import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Question
from app.db.session import get_session

router = APIRouter(prefix="/projects/{project_id}/questions", tags=["questions"])

class QuestionCreate(BaseModel):
    text: str
    reference_answer: str | None = None
    topic: str | None = None

class QuestionResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    text: str
    reference_answer: str | None = None
    topic: str | None = None

    model_config = {"from_attributes": True}

@router.post("/", response_model=QuestionResponse)
async def create_question(
        project_id: uuid.UUID,
        data: QuestionCreate,
        session: AsyncSession = Depends(get_session)
):
    question = Question(
        project_id=project_id,
        text=data.text,
        reference_answer=data.reference_answer,
        topic=data.topic
    )
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return question

@router.get("/", response_model=list[QuestionResponse])
async def get_questions(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    questions = await session.execute(select(Question).where(Question.project_id == project_id))
    return questions.scalars().all()

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
        project_id: uuid.UUID,
        question_id: uuid.UUID,
        session: AsyncSession = Depends(get_session)
):
    question = await session.get(Question, question_id)
    if not question or question.project_id != project_id:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.delete("/{question_id}")
async def delete_question(
        project_id: uuid.UUID,
        question_id: uuid.UUID,
        session: AsyncSession = Depends(get_session)
):
    question = await session.get(Question, question_id)
    if not question or question.project_id != project_id:
        raise HTTPException(status_code=404, detail="Question not found")
    await session.delete(question)
    await session.commit()
    return {"ok": True}