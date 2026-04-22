import re
import uuid
import jwt
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.models.hotel import Hotel
from app.core.config import get_settings
from app.core.security import get_jwks

settings = get_settings()

class AuthService:
    @staticmethod
    async def sync_user_identity(
        token: str, 
        user_id_or_sub: str, 
        session: AsyncSession
    ) -> Optional[User]:
        """
        Industry-grade identity linking and lazy profile creation.
        Handles Supabase identity transition to local DB.
        """
        jwks = get_jwks()
        try:
            payload = jwt.decode(
                token, 
                jwks if jwks else settings.SECRET_KEY, 
                algorithms=["ES256", "HS256", "RS256"], 
                options={"verify_aud": False}
            )
            email = payload.get("email")
            if not email:
                return None

            # 1. Check if email already exists (Identity Linking)
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if user:
                # Sync ID (e.g. from local integer/string to Supabase UUID)
                user.id = user_id_or_sub
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
            
            # 2. Lazy Creation (New User from Supabase)
            # Transaction block
            hotel_name = f"{email.split('@')[0]}'s Hotel"
            base_slug = re.sub(r'[^a-z0-9]', '-', hotel_name.lower()).strip('-')
            if not base_slug: base_slug = "hotel"
            
            # Slug collision check
            slug = base_slug
            result = await session.execute(select(Hotel).where(Hotel.slug == slug))
            if result.scalar_one_or_none():
                slug = f"{base_slug}-{str(uuid.uuid4())[:6]}"
            
            new_hotel = Hotel(name=hotel_name, slug=slug)
            session.add(new_hotel)
            await session.flush() # Get hotel ID without full commit yet
            
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
            return user

        except Exception as e:
            # Proper Production Logging would go here
            await session.rollback()
            return None
