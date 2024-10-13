from sqlalchemy.orm import Session
from app.services.email_services import verify_email_logic, password_reset_request_logic, reset_password_logic
from app.schemas.user_schema import ResetPassword

class EmailController:
    
    # Email Verification Route
    @staticmethod
    async def verify_email(token: str, db: Session, user):
        access_token = await verify_email_logic(token, db, user)  # Capture the access token
        print("This IS The result Fetched from Email Controller", access_token)
        return access_token  # Return the access token
    
    
    # Password Reset Request Route
    @staticmethod
    async def password_reset_request(email: str, db: Session):
        result = await password_reset_request_logic(email, db)
        return result
    
    
    # Route to Confirm Password Reset
    @staticmethod
    async def reset_password(token: str, new_password: ResetPassword, db: Session):
        result = await reset_password_logic(token, new_password.password, db)
        return result
