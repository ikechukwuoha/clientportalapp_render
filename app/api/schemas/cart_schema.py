from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

from sqlalchemy import UniqueConstraint

class AddItemSchema(BaseModel):
    user_id: UUID
    product_id: UUID
    quantity: int = Field(default=1, gt=0)
    
    __table_args__ = (UniqueConstraint('cart_id', 'item_id'),)


class UpdateQuantitySchema(BaseModel):
    user_id: UUID
    product_id: UUID
    quantity: int


# class CartItemSchema(BaseModel):
#     item_id: UUID
#     quantity: int
#     title: Optional[str]
#     shortDescription: Optional[str]
#     longDescription: Optional[str]
#     images: Optional[str]
    
class CartItemSchema(BaseModel):
    item_id: UUID
    quantity: int
    title: str
    shortDescription: Optional[str]
    longDescription: Optional[str]
    price: float
    total_price: float
    images: Optional[str]



class CartResponse(BaseModel):
    cart_id: UUID
    items: List[CartItemSchema]
    total_cost: float


class CheckoutResponse(BaseModel):
    message: str
    total_price: float
