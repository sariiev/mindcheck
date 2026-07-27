import uuid
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, Material
from app.db.session import get_session
from app.services.parser import parse_file
from app.services.vector_store import add_document, delete_document

router = APIRouter(prefix="/materials", tags=["materials"])

class MaterialResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}

@router.post("/", response_model=MaterialResponse)
async def upload_material(
        project_id: UUID,
        file: UploadFile = File(...),
        session: AsyncSession = Depends(get_session)
):
    content = await file.read()
    try:
        text = await parse_file(content, file.content_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=e)

    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    material = Material(
        project_id=project_id,
        name=file.filename,
    )

    session.add(material)
    await session.commit()
    await session.refresh(material)

    add_document(str(project_id), str(material.id), text)

    return material

@router.get("/", response_model=list[MaterialResponse])
async def get_materials(
        project_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    materials = await session.execute(
        select(Material)
        .where(Material.project_id == project_id)
        .order_by(Material.created_at.desc())
    )

    return materials.scalars().all()

@router.delete("/{material_id}")
async def delete_material(
        material_id: UUID,
        session: AsyncSession = Depends(get_session)
):
    material = await session.get(Material, material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")

    delete_document(str(material.project_id), str(material_id))

    await session.delete(material)
    await session.commit()
    return {"ok": True}