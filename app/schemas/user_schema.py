from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, field_validator, Field, EmailStr
import re
from pydantic import BaseModel, EmailStr, constr, Field

class UserCreate(BaseModel):
    first_name: str  # Type hint using constr directly
    last_name: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('password')
    def validate_password(cls, value):
        """
        Ensure password meets the specified requirements.
        """
        if len(value) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r"[A-Z]", value):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", value):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", value):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError('Password must contain at least one special character')
        return value

    class Config:
        from_attributes = True

    # Method for password confirmation validation
    @classmethod
    def validate_passwords(cls, password: str, password_confirm: str):
        if password != password_confirm:
            raise ValueError("Passwords do not match")




class User(BaseModel):
    id: int
    name:str
    email:str
    
    

class UserLogin(BaseModel):
    email: str
    password: str
    


# Response schema without the password
class UserResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        # Make sure Pydantic uses the correct types for serialization
        from_attributes = True


class SignupResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str