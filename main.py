# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timedelta
from typing import List, Optional

from database import get_db, init_db
from models import User, Request, Comment, SystemSettings, UserRole, UserStatus, RequestStatus, RequestType
from schemas import (
    UserCreate, UserInDB, UserPublic, UserUpdate, UserUpdateAdmin,
    RequestCreate, RequestUpdate, RequestAssign, RequestInDB, RequestWithDetails,
    CommentCreate, CommentInDB, CommentWithUser,
    LoginRequest, Token,
    SystemSettingUpdate, SystemSettingInDB,
    DashboardStats
)
from auth import (
    authenticate_user, create_access_token, get_password_hash,
    get_current_active_user, require_admin, require_manager, require_executor
)
from config import settings

# Create FastAPI app
app = FastAPI(
    title="Система управления заявками",
    description="API для системы управления заявками",
    version="1.0.0"
)

# CORS middleware
origins = [
    "http://localhost:5500",          # твой Live Server порт
    "http://127.0.0.1:5500",
    "http://localhost:3000",          # если используешь React/Vite и т.д.
    "http://127.0.0.1:3000",
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Потом указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Initialization ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    
    # Create default admin user if not exists
    db = next(get_db())
    try:
        admin = db.query(User).filter(User.username == "1488").first()
        if not admin:
            admin = User(
                username="1488",
                hashed_password=get_password_hash("0000"),
                fullname="Администратор Системы",
                address="Главный офис",
                role=UserRole.ADMIN,
                status=UserStatus.CONFIRMED,
                is_active=True
            )
            db.add(admin)
            db.commit()
            print("✓ Default admin user created (username: 1488, password: 0000)")
        
        # Create default system settings
        setting = db.query(SystemSettings).filter(SystemSettings.key == "response_time_hours").first()
        if not setting:
            setting = SystemSettings(
                key="response_time_hours",
                value="24",
                description="Время ответа на заявку (часы)"
            )
            db.add(setting)
            db.commit()
            print("✓ Default system settings created")
    finally:
        db.close()


# ==================== Health Check ====================

@app.get("/")
async def root():
    """API health check"""
    return {
        "status": "ok",
        "message": "УК ЖКХ API is running",
        "version": "1.0.0"
    }


# ==================== Authentication ====================

@app.post("/api/auth/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (client)
    """
    # Check if user already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this phone number already exists"
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        fullname=user_data.fullname,
        address=user_data.address,
        role=UserRole.CLIENT,
        status=UserStatus.CONFIRMED,
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@app.post("/api/auth/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Login and get JWT token
    """
    user = authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id, "role": user.role.value}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserInDB)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    Get current user information
    """
    return current_user


# ==================== Users ====================

@app.get("/api/users", response_model=List[UserInDB])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    status: Optional[UserStatus] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Get list of users (managers and admins only)
    """
    query = db.query(User)
    
    # Filter by role
    if role:
        query = query.filter(User.role == role)
    
    # Filter by status
    if status:
        query = query.filter(User.status == status)
    
    # Search by username or fullname
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.fullname.ilike(f"%{search}%")
            )
        )
    
    users = query.offset(skip).limit(limit).all()
    return users


@app.get("/api/users/{user_id}", response_model=UserInDB)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID
    """
    # Users can view their own profile, managers can view all
    if current_user.role not in [UserRole.ADMIN, UserRole.MANAGER] and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@app.put("/api/users/{user_id}", response_model=UserInDB)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update user information
    """
    # Users can update their own profile
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_update.fullname:
        user.fullname = user_update.fullname
    if user_update.address:
        user.address = user_update.address
    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)
    
    db.commit()
    db.refresh(user)
    
    return user


@app.put("/api/users/{user_id}/admin", response_model=UserInDB)
async def update_user_admin(
    user_id: int,
    user_update: UserUpdateAdmin,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user information (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    if user_update.fullname:
        user.fullname = user_update.fullname
    if user_update.address:
        user.address = user_update.address
    if user_update.password:
        user.hashed_password = get_password_hash(user_update.password)
    if user_update.role:
        user.role = user_update.role
    if user_update.status:
        user.status = user_update.status
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
    
    db.commit()
    db.refresh(user)
    
    return user


@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete user (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return None


# ==================== Requests ====================

@app.get("/api/requests", response_model=List[RequestWithDetails])
async def get_requests(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[RequestStatus] = None,
    type_filter: Optional[RequestType] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get list of requests
    """
    query = db.query(Request)
    
    # Clients see only their own requests
    if current_user.role == UserRole.CLIENT:
        query = query.filter(Request.client_id == current_user.id)
    
    # Executors see assigned requests
    elif current_user.role == UserRole.EXECUTOR:
        query = query.filter(Request.executor_id == current_user.id)
    
    # Managers and admins see all requests
    
    # Apply filters
    if status_filter:
        query = query.filter(Request.status == status_filter)
    
    if type_filter:
        query = query.filter(Request.type == type_filter)
    
    requests = query.order_by(Request.created_at.desc()).offset(skip).limit(limit).all()
    return requests


@app.get("/api/requests/{request_id}", response_model=RequestWithDetails)
async def get_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get request by ID
    """
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Check access rights
    if current_user.role == UserRole.CLIENT and request.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request"
        )
    
    if current_user.role == UserRole.EXECUTOR and request.executor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request"
        )
    
    return request


@app.post("/api/requests", response_model=RequestInDB, status_code=status.HTTP_201_CREATED)
async def create_request(
    request_data: RequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new request
    """
    # Get response time setting
    response_time_setting = db.query(SystemSettings).filter(
        SystemSettings.key == "response_time_hours"
    ).first()
    
    response_hours = int(response_time_setting.value) if response_time_setting else 24
    deadline = datetime.utcnow() + timedelta(hours=response_hours)
    
    new_request = Request(
        client_id=current_user.id,
        type=request_data.type,
        description=request_data.description,
        status=RequestStatus.NEW,
        priority=1,
        deadline=deadline
    )
    
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    
    return new_request


@app.put("/api/requests/{request_id}", response_model=RequestInDB)
async def update_request(
    request_id: int,
    request_update: RequestUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update request
    """
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Check permissions
    is_owner = request.client_id == current_user.id
    is_executor = request.executor_id == current_user.id
    is_manager = current_user.role in [UserRole.ADMIN, UserRole.MANAGER]
    
    if not (is_owner or is_executor or is_manager):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this request"
        )
    
    # Update fields
    if request_update.description and is_owner:
        request.description = request_update.description
    
    if request_update.status:
        request.status = request_update.status
        
        if request_update.status == RequestStatus.IN_PROGRESS and not request.started_at:
            request.started_at = datetime.utcnow()
        
        if request_update.status == RequestStatus.COMPLETED and not request.completed_at:
            request.completed_at = datetime.utcnow()
    
    if request_update.priority and is_manager:
        request.priority = request_update.priority
    
    db.commit()
    db.refresh(request)
    
    return request


@app.post("/api/requests/{request_id}/assign", response_model=RequestInDB)
async def assign_request(
    request_id: int,
    assign_data: RequestAssign,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Assign executor to request (managers and admins only)
    """
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Check if executor exists and has executor role
    executor = db.query(User).filter(User.id == assign_data.executor_id).first()
    if not executor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Executor not found"
        )
    
    if executor.role != UserRole.EXECUTOR:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not an executor"
        )
    
    # Assign executor
    request.executor_id = assign_data.executor_id
    request.status = RequestStatus.ASSIGNED
    request.assigned_at = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    
    return request


@app.delete("/api/requests/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_request(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete request
    """
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Only client who created or admin can delete
    if request.client_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this request"
        )
    
    db.delete(request)
    db.commit()
    
    return None


# ==================== Comments ====================

@app.get("/api/requests/{request_id}/comments", response_model=List[CommentWithUser])
async def get_request_comments(
    request_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get comments for a request
    """
    # Check if request exists and user has access
    request = db.query(Request).filter(Request.id == request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Check access rights
    if current_user.role == UserRole.CLIENT and request.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view comments for this request"
        )
    
    comments = db.query(Comment).filter(Comment.request_id == request_id).order_by(Comment.created_at).all()
    return comments


@app.post("/api/comments", response_model=CommentInDB, status_code=status.HTTP_201_CREATED)
async def create_comment(
    comment_data: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a comment on a request
    """
    # Check if request exists
    request = db.query(Request).filter(Request.id == comment_data.request_id).first()
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    
    # Check access rights
    if current_user.role == UserRole.CLIENT and request.client_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to comment on this request"
        )
    
    if current_user.role == UserRole.EXECUTOR and request.executor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to comment on this request"
        )
    
    new_comment = Comment(
        request_id=comment_data.request_id,
        user_id=current_user.id,
        text=comment_data.text
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return new_comment


# ==================== Statistics ====================

@app.get("/api/stats/dashboard", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics (managers and admins only)
    """
    total_requests = db.query(func.count(Request.id)).scalar()
    new_requests = db.query(func.count(Request.id)).filter(Request.status == RequestStatus.NEW).scalar()
    in_progress_requests = db.query(func.count(Request.id)).filter(
        Request.status.in_([RequestStatus.ASSIGNED, RequestStatus.IN_PROGRESS])
    ).scalar()
    completed_requests = db.query(func.count(Request.id)).filter(Request.status == RequestStatus.COMPLETED).scalar()
    
    total_users = db.query(func.count(User.id)).scalar()
    total_clients = db.query(func.count(User.id)).filter(User.role == UserRole.CLIENT).scalar()
    total_executors = db.query(func.count(User.id)).filter(User.role == UserRole.EXECUTOR).scalar()
    
    return DashboardStats(
        total_requests=total_requests,
        new_requests=new_requests,
        in_progress_requests=in_progress_requests,
        completed_requests=completed_requests,
        total_users=total_users,
        total_clients=total_clients,
        total_executors=total_executors
    )


# ==================== System Settings ====================

@app.get("/api/settings", response_model=List[SystemSettingInDB])
async def get_settings(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all system settings (admins only)
    """
    settings = db.query(SystemSettings).all()
    return settings


@app.put("/api/settings/{setting_key}", response_model=SystemSettingInDB)
async def update_setting(
    setting_key: str,
    setting_update: SystemSettingUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update system setting (admins only)
    """
    setting = db.query(SystemSettings).filter(SystemSettings.key == setting_key).first()
    if not setting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Setting not found"
        )
    
    setting.value = setting_update.value
    
    db.commit()
    db.refresh(setting)
    
    return setting


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )
