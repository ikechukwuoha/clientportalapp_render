from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from jose import JWTError, ExpiredSignatureError, jwt
from app.config.settings import settings
from app.database.db import get_db
from app.models.user_model import User
from app.security.security import create_access_token
from app.services.email_services import EmailService

router = APIRouter()
email_service = EmailService()

@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db), response: Response = None):  # Include response here
    try:
        # Decode the token and check for errors
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")

        # Check if the user exists in the database
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        # Check if the email is already verified
        if user.is_active:
            raise HTTPException(status_code=400, detail="This account is already verified")
        
        # Update the user's active status
        user.is_active = True
        db.commit()
        
        token_data = {
            "message": "Email verified successfully",
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "is_active": user.is_active
        }
        token = create_access_token(data=token_data)

        # Set the token in the cookie
        response.set_cookie(key="access_token", value=token, httponly=True, samesite='Strict')

        return {"message": "Email verified successfully"}
    
    except ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
