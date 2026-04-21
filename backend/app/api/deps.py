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
    
    # 3. Fallback: Agar ID se nahi mila, toh Email se dhundho (Identity Linking)
    if user is None:
        jwks = get_jwks()
        try:
            payload = jwt.decode(
                token, 
                jwks if jwks else settings.SECRET_KEY, 
                algorithms=["ES256", "HS256", "RS256"], 
                options={"verify_aud": False}
            )
            email = payload.get("email")
            
            if email:
                # Pehle Email se check karo (Identity Linking)
                result = await session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                
                if user:
                    # Sync ID
                    user.id = user_id_or_sub
                    session.add(user)
                    await session.commit()
                    await session.refresh(user)
                else:
                    # LAZY CREATE
                    from app.models.hotel import Hotel
                    from app.models.user import UserRole
                    import re
                    import uuid
                    
                    try:
                        # 1. Create a default hotel
                        hotel_name = f"{email.split('@')[0]}'s Hotel"
                        base_slug = re.sub(r'[^a-z0-9]', '-', hotel_name.lower()).strip('-')
                        if not base_slug: base_slug = "hotel"
                        
                        slug = base_slug
                        # Check slug collision
                        result = await session.execute(select(Hotel).where(Hotel.slug == slug))
                        if result.scalar_one_or_none():
                            slug = f"{base_slug}-{str(uuid.uuid4())[:6]}"
                        
                        new_hotel = Hotel(name=hotel_name, slug=slug)
                        session.add(new_hotel)
                        await session.flush()
                        
                        # 2. Create the user
                        user = User(
                            id=user_id_or_sub,
                            email=email,
                            name=email.split('@')[0].capitalize(),
                            hashed_password="SUPABASE_AUTH",
                            role=UserRole.OWNER,
                            hotel_id=new_hotel.id
                        )
                        session.add(user)
                        await session.commit()
                        await session.refresh(user)
                    except Exception as inner_e:
                        await session.rollback()
                        print(f"Lazy create transaction failed: {inner_e}")
                        user = None
        except Exception as e:
            print(f"Lazy/Linking failed: {e}")
            pass

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
