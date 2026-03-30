from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import (
    select
)
from models import User
from schemas.schemas import BaseUser

async def make_user(session: AsyncSession, load: BaseUser) -> bool:
    try:
        stmt = User(user_id=load.user_id, username=load.username, password=load.password)
        session.add(stmt)
        await session.commit()
        return True
    except Exception as e:
        return False


async def select_user_by_id(
    session: AsyncSession,
    id: int
):
    stmt = select(User).where(User.user_id == id)
    res = await session.execute(stmt)
    user = res.scalar_one_or_none()
    return user