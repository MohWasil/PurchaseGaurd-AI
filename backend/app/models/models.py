"""
Database Models - SQLAlchemy
Secure, production-ready schema for PurchaseGuard AI
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    """User authentication model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    purchases = relationship("Purchase", back_populates="user", cascade="all, delete-orphan")

class Purchase(Base):
    """Purchase/Receipt model - encrypted sensitive data"""
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic info (not sensitive)
    merchant_name = Column(String(255), nullable=False)
    purchase_date = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    
    # Deadlines (calculated)
    return_deadline = Column(DateTime, nullable=True)
    warranty_expiry = Column(DateTime, nullable=True)
    
    # Status tracking
    is_returned = Column(Boolean, default=False)
    is_claimed = Column(Boolean, default=False)
    
    # File references (encrypted paths)
    receipt_path = Column(String(500), nullable=True)
    encrypted_data = Column(Text, nullable=True)  # Encrypted receipt details
    
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    user = relationship("User", back_populates="purchases")

class Alert(Base):
    """Alert/Notification model"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=True)
    
    alert_type = Column(String(50), nullable=False) 
    message = Column(Text, nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    
    user = relationship("User")
    purchase = relationship("Purchase")