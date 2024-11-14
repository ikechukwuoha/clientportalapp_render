# Performs Low Level Crud Opperations to The DataBase

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.models.user_model import User  # Ensure you import your User model
from app.api.schemas.user_schema import UserCreate  # Define your UserCreate schema



async def create_user(db: AsyncSession, user: UserCreate):
    db_user = User(**user.model_dump())  # Use model_dump instead of dict
    db.add(db_user)
    await db.commit()  # Ensure to await commit
    await db.refresh(db_user)  # Optional: to refresh instance with updated state
    return db_user





async def get_user_by_email(db: AsyncSession, email: str) -> User:
    stmt = select(User).where(User.email == email)  # Use where() instead of filter()
    result = await db.execute(stmt)
    return result.scalars().first()  # Use scalars() to retrieve the first result
