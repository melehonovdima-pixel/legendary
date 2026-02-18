from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List
from models import UserRole, UserStatus, RequestStatus, RequestType


# ==================== User Schemas ====================

class UserBase(BaseModel):
    username: str
    fullname: str
    address: Optional[str] = None


class UserCreate(BaseModel): #Регистрация
    username: str = Field(..., min_length=11, max_length=11, description="Phone number (11 digits)")
    fullname: str = Field(..., min_length=3, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    password: str = Field(..., min_length=6, max_length=100)



class UserUpdate(BaseModel):
    """Schema for updating user data"""
    fullname: Optional[str] = Field(None, min_length=3, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserUpdateAdmin(UserUpdate):
    """Schema for admin to update user data"""
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """User schema from database"""
    id: int
    role: UserRole
    status: UserStatus
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    """Public user information (without sensitive data)"""
    id: int
    username: str
    fullname: str
    address: Optional[str] = None
    role: UserRole
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Request Schemas ====================

class RequestBase(BaseModel):
    """Base request schema"""
    type: RequestType
    description: str = Field(..., min_length=10, max_length=2000)


class RequestCreate(RequestBase):
    """Schema for creating new request"""
    pass


class RequestUpdate(BaseModel):
    """Schema for updating request"""
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    status: Optional[RequestStatus] = None
    priority: Optional[int] = Field(None, ge=1, le=3)


class RequestAssign(BaseModel):
    """Schema for assigning executor to request"""
    executor_id: int


class RequestInDB(RequestBase):
    """Request schema from database"""
    id: int
    client_id: int
    executor_id: Optional[int] = None
    status: RequestStatus
    priority: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class RequestWithDetails(RequestInDB):
    """Request with related user information"""
    client: UserPublic
    executor: Optional[UserPublic] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Comment Schemas ====================

class CommentBase(BaseModel):
    """Base comment schema"""
    text: str = Field(..., min_length=1, max_length=1000)


class CommentCreate(CommentBase):
    """Schema for creating comment"""
    request_id: int


class CommentInDB(CommentBase):
    """Comment schema from database"""
    id: int
    request_id: int
    user_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CommentWithUser(CommentInDB):
    """Comment with user information"""
    user: UserPublic
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Auth Schemas ====================

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data stored in JWT token"""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Login credentials"""
    username: str
    password: str


# ==================== System Settings Schemas ====================

class SystemSettingUpdate(BaseModel):
    """Schema for updating system setting"""
    value: str


class SystemSettingInDB(BaseModel):
    """System setting from database"""
    id: int
    key: str
    value: str
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Statistics Schemas ====================

class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_requests: int
    new_requests: int
    in_progress_requests: int
    completed_requests: int
    total_users: int
    total_clients: int
    total_executors: int
