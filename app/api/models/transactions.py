from sqlalchemy import BigInteger, Column, Float, String, DateTime, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.api.models import Base
import uuid

class UserTransactions(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    plan = Column(String, nullable=False)
    payment_status = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    country = Column(String, nullable=False)
    company_name = Column(String, nullable=False)
    organization = Column(String, nullable=False)
    site_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    training_and_setup = Column(Boolean, nullable=False)
    valid_from = Column(DateTime, nullable=False)
    valid_upto = Column(DateTime, nullable=False)
    payment_reference = Column(String, nullable=False)
    transaction_id = Column(BigInteger, nullable=False)
    message = Column(String, nullable=False)
    paystack_status = Column(String)
    paystack_response = Column(JSON)
    
    
    site_creation_status = Column(String)
    site_creation_job_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    site_creation_error = Column(String)
    

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Define relationship with User
    user = relationship("User", back_populates="transactions")
