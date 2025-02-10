from pydantic import BaseModel, UUID4
from typing import Optional

class CardBase(BaseModel):
    card_number: str
    card_name: str
    expiry_date: str
    cvv: str
    is_default: bool = False  # Default value

class CardCreate(CardBase):
    pass

class CardUpdate(BaseModel):
    card_number: Optional[str] = None
    card_name: Optional[str] = None
    expiry_date: Optional[str] = None
    cvv: Optional[str] = None
    is_default: Optional[bool] = None  # Allow updating default status

    class Config:
        orm_mode = True

class CardResponse(CardBase):
    id: UUID4
    user_id: UUID4

    class Config:
        orm_mode = True