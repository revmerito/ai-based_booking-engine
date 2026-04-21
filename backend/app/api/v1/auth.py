"""
Authentication Router
Login, Signup, Refresh token endpoints.
Frontend ke auth.ts aur client.ts se match karta hai.
"""
from datetime import timedelta
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
import re
import uuid

from app.core.database import get_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_reset_token,
    verify_password,
    get_password_hash,
    verify_token
)
from app.core.config import get_settings
from app.models.user import User, UserCreate, UserRead, UserRole
from app.models.hotel import Hotel
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


def generate_slug(name: str) -> str:
    """Hotel name se URL-friendly slug banata hai"""
    slug = name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    return slug


class LoginRequest(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login")
async def login(
    login_data: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    User login - JSON flow.
    Frontend sends email and password in JSON body.
    """
    # 1. Database se pucho: "Kya is email ID ka banda hai tumhare paas?"
    # Hum 'User' table mein dhundh rahe hain jaha user.email match kare.
    result = await session.execute(
        select(User).where(User.email == login_data.email)
    )
    user = result.scalar_one_or_none() # Banda mila ya nahi?
    
    # 2. Check karo: Banda nahi mila OR Password galat hai?
    # verify_password() function encrypted password ko match karta hai.
    if not user or not verify_password(login_data.password, user.hashed_password):
        # Agar galat hai, toh 401 Unauthorized error feko.
        # Security Tip: Ye mat batao ki email galat thha ya password, bas bolo "Invalid credentials".
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 3. Check karo: Kya iska account active hai?
    # Agar admin ne ban kiya hai, toh login mat karne do.
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # 4. Success! Ab iske liye VIP Pass (Token) banao.
    # Access Token: Short-term pass (e.g. 30 mins) API use karne ke liye.
    access_token = create_access_token(user.id)
    
    # Refresh Token: Long-term pass (e.g. 7 days) naya access token lene ke liye.
    refresh_token = create_refresh_token(user.id)
    
    # 5. Frontend ko Jawab (Response) bhejo.
    # Ab frontend is token ko save kar lega.
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/signup")
async def signup(
    user_data: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    New user + hotel registration.
    Supports Supabase Auth: User already exists in Supabase, now creating local profile.
    """
    try:
        # 1. Check if user already exists in local DB (by email)
        result = await session.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # Sync UUID if provided and different
            if user_data.id and existing_user.id != user_data.id:
                existing_user.id = user_data.id
                session.add(existing_user)
                await session.commit()
                await session.refresh(existing_user)
                
            return {
                "user": UserRead.model_validate(existing_user).model_dump(),
                "message": "User already exists and was synced"
            }
        
        # 2. Create hotel with unique slug
        base_slug = generate_slug(user_data.hotel_name)
        if not base_slug:
            base_slug = "hotel-" + str(uuid.uuid4())[:8]
            
        hotel_slug = base_slug
        
        # Check if slug exists
        result = await session.execute(
            select(Hotel).where(Hotel.slug == hotel_slug)
        )
        if result.scalar_one_or_none():
            hotel_slug = f"{base_slug}-{str(uuid.uuid4())[:6]}"
        
        hotel = Hotel(
            name=user_data.hotel_name,
            slug=hotel_slug
        )
        session.add(hotel)
        await session.flush()
        
        # 3. Create user
        user_id = user_data.id or str(uuid.uuid4())
        user = User(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            hashed_password="SUPABASE_AUTH",
            role=UserRole.OWNER,
            hotel_id=hotel.id
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        return {
            "user": UserRead.model_validate(user).model_dump()
        }
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/refresh")
async def refresh_token(
    refresh_data: dict,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Refresh token se new access token lena.
    Frontend client.ts mein tryRefreshToken function isko call karta hai.
    """
    refresh_token = refresh_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token required"
        )
    
    # Verify refresh token
    user_id = verify_token(refresh_token, "refresh")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Verify user still exists and is active
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new tokens
    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Password reset request.
    Generates a token and logically sends email (logged to console for now).
    """
    result = await session.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user:
        # Security: Don't reveal if user doesn't exist
        return {"message": "If this email is registered, you will receive password reset instructions."}
    
    # Generate a short-lived reset token
    # Using specific 'reset' type for security
    reset_token = create_reset_token(user.id, expires_delta=timedelta(minutes=15))
    
    # LOGGING THE TOKEN FOR DEBUGGING/DEV
    print(f"--- PASSWORD RESET TOKEN FOR {user.email} ---")
    print(reset_token)
    print("---------------------------------------------")
    
    # Save to file for AI agent to read easily
    with open("reset_token.txt", "w") as f:
        f.write(reset_token)

    return {"message": "If this email is registered, you will receive password reset instructions."}


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Reset password using token.
    """
    user_id = verify_token(request.token, "reset") # Verify specifically for reset type
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user account"
        )

    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    session.add(user)
    await session.commit()

    return {"message": "Password updated successfully"}


from app.api.deps import get_current_user

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)]
):
    """
    Change password for logged in user.
    """
    if not verify_password(request.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_user.hashed_password = get_password_hash(request.new_password)
    session.add(current_user)
    await session.commit()

    return {"message": "Password updated successfully"}
