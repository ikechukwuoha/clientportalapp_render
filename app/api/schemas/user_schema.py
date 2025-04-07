from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from passlib.context import CryptContext
from pydantic import BaseModel, field_validator, Field, EmailStr, UUID4, field_validator
import re
import uuid
from pydantic import BaseModel, EmailStr, constr, Field,field_serializer, HttpUrl

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
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True
    
    

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
        
    # Serializers for UUID and datetime
    @field_serializer('id')
    def serialize_uuid(self, value: UUID) -> str:
        return str(value)

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()

class SignupResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str

class ResetPassword(BaseModel):
    password: str

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    

class PasswordResetConfirmModel(BaseModel):
    new_password: str
    
    
    
class Email(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
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
    

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    country: Optional[str] = None
    role_id: Optional[UUID4] = None 
    is_active: Optional[bool] = None
    
    email: Optional[str] = Field(
        None,
        description="Email cannot be updated after registration, Please contact Admin",
        frozen=True
    )
    
    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
        from_attributes=True,  # Moved from Config class
        arbitrary_types_allowed=True  # Moved from Config class
    )

    @field_validator('*', mode='before')
    def convert_empty_to_none(cls, value):
        if value == "":
            return None
        return value

    @field_validator("email", mode="before")
    def validate_email(cls, value):
        if value == "":
            return None
        return value

    @field_validator("role_id", mode="before")
    def validate_role_id(cls, value):
        if value == "":
            return None
        return value

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class ChangePassword(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=50)
    new_password: str = Field(..., min_length=6, max_length=50)
    confirm_password: str = Field(..., min_length=6, max_length=50)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash the password using bcrypt."""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify the password against the stored hash."""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def validate_new_password(new_password: str, confirm_password: str):
        """Ensure new password and confirm password match."""
        if new_password != confirm_password:
            raise ValueError("New password and confirmation do not match.")