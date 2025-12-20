"""
Authentication endpoints.

Security Rules:
- POST /auth/login: Public endpoint for user authentication
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.user import User
from schemas.auth import LoginRequest, LoginResponse
from core.security import verify_password, create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    
    Security: Public endpoint.
    
    Args:
        login_data: Login credentials (username, password)
        db: Database session
        
    Returns:
        LoginResponse with access_token and user data
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Find user by username (exclude soft-deleted users)
    result = await db.execute(
        select(User).where(
            User.username == login_data.username,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token
    access_token = create_access_token(data={"sub": user.username})
    
    logger.info(f"User {user.username} logged in successfully")
    
    # Return token and user data
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user,  # UserRead schema will be serialized automatically
    )
