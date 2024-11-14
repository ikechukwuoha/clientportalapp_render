from sqlalchemy import Column, String, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.api.models import Base
import uuid
from sqlalchemy.dialects.postgresql import UUID



# Permission model
class Permission(Base):
    __tablename__ = "permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, index=True)

    # This relationship is the inverse of the role's permissions relationship
    roles = relationship("Role", secondary="role_permissions", back_populates="permissions")



    # Many-to-many relationship with users
    users = relationship("User", secondary='user_permissions', back_populates="permissions")