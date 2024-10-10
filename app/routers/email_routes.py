from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from app.database import get_db
from app.models import User
from app.services.email_services import EmailService

router = APIRouter()
email_service = EmailService()




@router.get("/verify-email")
async def verify_email(token: str, db: Session = Depends(get_db)):
    print("Endpoint hit")
    try:
        payload = jwt.decode(token, email_service.SECRET_KEY, algorithms=[email_service.ALGORITHM])
        email = payload.get("email")
        if email is None:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=400, detail="User not found")
        
        user.is_active = True
        db.commit()
        return {"message": "Email verified successfully"}
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid token")
