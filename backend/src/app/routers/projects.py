import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project
from app.db.session import get_session

router = APIRouter(prefix="/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    strictness: int | None = Field(default=5, ge=1, le=10)

class ProjectResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str| None = None
    strictness: int | None = None

    model_config = {"from_attributes": True}

@router.post("/", response_model=ProjectResponse)
async def create_project(data: ProjectCreate, session: AsyncSession = Depends(get_session)):
    project = Project(name=data.name, description=data.description, strictness=data.strictness)
    session.add(project)
    await session.commit()
    await session.refresh(project)
    return project

@router.get("/", response_model=list[ProjectResponse])
async def get_projects(session: AsyncSession = Depends(get_session)):
    projects = await session.execute(select(Project))
    return projects.scalars().all()

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
        project_id: uuid.UUID,
        data: ProjectCreate,
        session: AsyncSession = Depends(get_session)
):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.name = data.name
    project.description = data.description
    project.strictness = data.strictness
    await session.commit()
    await session.refresh(project)
    return project

@router.delete("/{project_id}")
async def delete_project(project_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await session.delete(project)
    await session.commit()
    return {"ok": True}