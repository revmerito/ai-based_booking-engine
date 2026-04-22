"""
Authentication Dependencies
Protected routes ke liye current user retrieve karta hai.
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.core.security import verify_token
from app.models.user import User

# OAuth2 scheme - Frontend Authorization header se token extract karega
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    """
    Token verify karke current user return karta hai.
    Supabase identity handling added.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # 1. Token verify karo (Symmetric or Asymmetric)
    # verify_token might return Supabase sub (UUID) or our local ID
    user_id_or_sub = verify_token(token, "access")
    if user_id_or_sub is None:
        raise credentials_exception
    
    # 2. User database se fetch karo - Pehle ID se (Exact match)
    result = await session.execute(select(User).where(User.id == user_id_or_sub))
    user = result.scalar_one_or_none()
    
    # 3. Fallback: Agar ID se nahi mila, toh Identity Syncing/Linking (AuthService)
    if user is None:
        from app.services.auth_service import AuthService
        user = await AuthService.sync_user_identity(token, user_id_or_sub, session)

    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is deactivated"
        )
    
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """Shortcut dependency for active user"""
    return current_user


# Type alias for cleaner route signatures
CurrentUser = Annotated[User, Depends(get_current_active_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
