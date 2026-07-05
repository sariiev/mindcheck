from app.db.models import Base, Project, Question, Answer
from app.db.session import get_session, engine


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)