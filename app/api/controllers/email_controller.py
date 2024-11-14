from datetime import datetime
from fastapi import HTTPException
from jose import JWTError
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.config.settings import settings
from app.api.models.user_model import User
from app.api.security.security import hash_password
from app.api.services.email_services import verify_email_logic, password_reset_request_logic, reset_password_logic
from app.api.schemas.user_schema import ResetPassword
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone


class EmailController:



    @staticmethod
    async def verify_email(db: AsyncSession, user: User):
        try:
            # Activate user
            user.is_active = True
            await db.commit()

        except HTTPException as e:
            raise e
        except Exception as e:
            # Rollback the transaction in case of any errors
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
        finally:
            # Close the session
            await db.close()




    
    
    # Password Reset Request Route
    @staticmethod
    async def password_reset_request(email: str, db: AsyncSession):
        result = await password_reset_request_logic(email, db)
        return result



    
    
    # Route to Confirm Password Reset
    @staticmethod
    async def reset_password(user: User, new_password: ResetPassword, db: AsyncSession):
        await reset_password_logic(user.email, new_password.password, db)

