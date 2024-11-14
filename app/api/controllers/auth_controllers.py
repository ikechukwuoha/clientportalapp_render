from sqlalchemy.orm import Session
from app.api.services.user_services import signup, signin
from app.api.schemas.user_schema import UserCreate, UserLogin

class AuthController:
    
    @staticmethod
    async def register_user(db: Session, user: UserCreate):
        """
        Calls the signup service to handle user registration logic.
        """
        result = await signup(db, user)
        return result
    

    @staticmethod
    async def login_user(db: Session, user: UserLogin):
        """
        Calls the signin service to handle user login logic.
        """
        result = await signin(db, user)
        return result
