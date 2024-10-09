# Performs Low Level Crud Opperations to The DataBase

from sqlalchemy.orm import Session
from app.models.user_model import User  # Ensure you import your User model
from app.schemas.user_schema import UserCreate  # Define your UserCreate schema

def create_user(db: Session, user: UserCreate) -> User:
    db_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=user.password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()
