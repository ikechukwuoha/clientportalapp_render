import uuid
from sqlalchemy import Column, Float, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.api.models import Base
from uuid import uuid4
from app.api.models.product import Product


class Cart(Base):
    __tablename__ = 'carts'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship('User', back_populates='cart')
    items = relationship('CartItem', back_populates='cart', cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = 'cart_items'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    cart_id = Column(UUID(as_uuid=True), ForeignKey('carts.id'), nullable=False)
    item_id = Column(UUID(as_uuid=True), ForeignKey('products.id'), nullable=False)
    title = Column(String, nullable=True)
    price = Column(Float, nullable=False, default=0.00)
    quantity = Column(Integer, nullable=False, default=1)
    short_description = Column(String, name='shortDescription', nullable=True)
    long_description = Column(String, name='longDescription', nullable=True)
    images = Column(String, nullable=True)

    # Relationships
    cart = relationship('Cart', back_populates='items')
    product = relationship('Product', back_populates='cart_items')
