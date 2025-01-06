import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.api.models import Base
from uuid import uuid4



class User(Base):
    __tablename__ = 'users'

  
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"))
    password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)



    # Relationship with Role (many-to-one)
    role = relationship("Role", back_populates="users")
    
    # Many-to-many relationship with permissions
    permissions = relationship("Permission", secondary='user_permissions', back_populates="users")
    
