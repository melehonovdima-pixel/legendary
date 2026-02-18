from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class UserRole(str, enum.Enum):
    """User roles in the system"""
    CLIENT = "client"
    EXECUTOR = "executor"
    MANAGER = "manager"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    """User account status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    BLOCKED = "blocked"


class RequestStatus(str, enum.Enum):
    """Request status"""
    NEW = "new"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RequestType(str, enum.Enum):
    """Types of problems/requests"""
    PLUMBING = "plumbing"
    ELECTRICITY = "electricity"
    ELEVATOR = "elevator"
    CLEANING = "cleaning"
    HEATING = "heating"
    OTHER = "other"


class User(Base):
    """User model - represents all types of users in the system"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)  # Phone number
    hashed_password = Column(String(255), nullable=False)
    fullname = Column(String(255), nullable=False)
    address = Column(String(500))
    role = Column(Enum(UserRole), default=UserRole.CLIENT, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.CONFIRMED, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    requests = relationship("Request", back_populates="client", foreign_keys="Request.client_id")
    assigned_requests = relationship("Request", back_populates="executor", foreign_keys="Request.executor_id")
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class Request(Base):
    """Request model - service requests from clients"""
    __tablename__ = "requests"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    executor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    type = Column(Enum(RequestType), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(RequestStatus), default=RequestStatus.NEW, nullable=False)
    
    priority = Column(Integer, default=1)  # 1=normal, 2=high, 3=urgent
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    deadline = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    client = relationship("User", back_populates="requests", foreign_keys=[client_id])
    executor = relationship("User", back_populates="assigned_requests", foreign_keys=[executor_id])
    comments = relationship("Comment", back_populates="request", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Request(id={self.id}, type={self.type}, status={self.status})>"


class Comment(Base):
    """Comment model - comments on requests"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("requests.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request = relationship("Request", back_populates="comments")
    user = relationship("User")
    
    def __repr__(self):
        return f"<Comment(id={self.id}, request_id={self.request_id})>"


class SystemSettings(Base):
    """System settings table"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(500), nullable=False)
    description = Column(String(500))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<SystemSettings(key={self.key}, value={self.value})>"
