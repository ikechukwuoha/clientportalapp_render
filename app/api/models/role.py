from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from app.api.models import Base
from app.api.models.role_permission import role_permissions
import uuid
from sqlalchemy.dialects.postgresql import UUID



# Role model
class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)

    # Relationship with Permission (many-to-many)
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

    # Relationship with User (many-to-many)
    users = relationship("User", back_populates="role")
