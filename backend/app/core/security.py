"""
Security Utilities
JWT Token generation aur verification yahan hoti hai.
Password hashing bhi yahan handle hota hai.
"""
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import get_settings

import requests
from functools import lru_cache

settings = get_settings()

@lru_cache()
def get_jwks():
    """Fetches Supabase JWKS for ECC verification"""
    if not settings.SUPABASE_JWKS_URL:
        # print("No SUPABASE_JWKS_URL configured")
        return None
    try:
        # print(f"Fetching JWKS from {settings.SUPABASE_JWKS_URL}...")
        response = requests.get(settings.SUPABASE_JWKS_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching JWKS: {e}")
        return None

# Password hashing context - bcrypt use kar rahe hain (industry standard)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """
    Access token banata hai jo short-lived hota hai.
    Subject usually user_id hota hai.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(subject: str | Any) -> str:
    """
    Refresh token banata hai jo long-lived hota hai.
    Isse new access token lene ke liye use karte hain.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_reset_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """
    Password reset token banata hai.
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15) # Default 15 mins

    to_encode = {"exp": expire, "sub": str(subject), "type": "reset"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> str | None:
    """
    Token verify karta hai aur subject (user_id) return karta hai.
    Supabase (ECC) aur Local (HS256) dono support karta hai.
    """
    # 1. Try Local JWT first (for backward compatibility or local tokens)
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Local tokens usually have a 'type' claim we added
        if payload.get("type") == token_type:
            return payload.get("sub")
    except JWTError:
        pass

    # 2. Try Supabase JWT (RS256/ES256 via JWKS)
    jwks = get_jwks()
    if jwks:
        try:
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            
            # Find the correct key in JWKS
            key_data = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    key_data = key
                    break
            
            if key_data:
                # Construct the key and decode
                from jose import jwk
                public_key = jwk.construct(key_data)
                payload = jwt.decode(
                    token, 
                    public_key, 
                    algorithms=["ES256", "RS256"],
                    options={
                        "verify_aud": False,
                        "verify_sub": True,
                        "verify_iat": True,
                        "verify_exp": True,
                        "verify_nbf": True,
                    }
                )
                return payload.get("sub")
        except JWTError:
             pass
        except Exception:
             pass

    return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    User ka password verify karta hai.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Password ko hash karta hai storage ke liye.
    """
    return pwd_context.hash(password)
