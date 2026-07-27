import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Question, Project
from app.db.session import get_session

router = APIRouter(prefix="/questions", tags=["questions"])

class QuestionCreate(BaseModel):
    project_id: uuid.UUID
    text: str = Field(max_length=1000)
    reference_answer: str | None = Field(default=None, max_length=3000)
    topic: str | None = Field(default=None, max_length=255)

class QuestionBulkCreateItem(BaseModel):
    text: str = Field(max_length=1000)
    reference_answer: str | None = Field(default=None, max_length=3000)
    topic: str | None = Field(default=None, max_length=255)

class QuestionUpdate(BaseModel):
    text: str = Field(max_length=1000)
    reference_answer: str | None = Field(default=None, max_length=3000)
    topic: str | None = Field(default=None, max_length=255)

class QuestionResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    text: str
    reference_answer: str | None = None
    topic: str | None = None

    model_config = {"from_attributes": True}

@router.post("/", response_model=QuestionResponse)
async def create_question(
        data: QuestionCreate,
        session: AsyncSession = Depends(get_session)
):
    question = Question(
        project_id=data.project_id,
        text=data.text,
        reference_answer=data.reference_answer,
        topic=data.topic
    )
    session.add(question)
    await session.commit()
    await session.refresh(question)
    return question

@router.post("/bulk", response_model=list[QuestionResponse])
async def bulk_create_questions(
        project_id: uuid.UUID,
        data: list[QuestionBulkCreateItem],
        session: AsyncSession = Depends(get_session)
):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    questions = [
        Question(
            project_id=project_id,
            text=question.text,
            reference_answer=question.reference_answer,
            topic=question.topic
        )
        for question in data
    ]

    session.add_all(questions)
    await session.commit()
    for question in questions:
        await session.refresh(question)
    return questions

@router.get("/", response_model=list[QuestionResponse])
async def get_questions(
        project_id: uuid.UUID = None,
        session: AsyncSession = Depends(get_session)
):
    query = select(Question)
    if project_id is not None:
        query = query.where(Question.project_id == project_id)

    questions = await session.execute(query)
    return questions.scalars().all()

@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
        question_id: uuid.UUID,
        session: AsyncSession = Depends(get_session)
):
    question = await session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    return question

@router.put("/{question_id}", response_model=QuestionResponse)
async def update_question(
        question_id: uuid.UUID,
        data: QuestionUpdate,
        session: AsyncSession = Depends(get_session)
):
    question = await session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    question.text = data.text
    question.reference_answer = data.reference_answer
    question.topic = data.topic
    await session.commit()
    await session.refresh(question)
    return question

@router.delete("/{question_id}")
async def delete_question(
        question_id: uuid.UUID,
        session: AsyncSession = Depends(get_session)
):
    question = await session.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    await session.delete(question)
    await session.commit()
    return {"ok": True}