"""
Integration API Endpoints
Manage API keys, widget code, and integration settings
"""
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status, Depends
from sqlmodel import select
import secrets
import hashlib

from app.api.deps import CurrentUser, DbSession
from app.models.integration import (
    APIKey, APIKeyCreate, APIKeyRead, APIKeyWithSecret,
    IntegrationSettings, IntegrationSettingsRead, IntegrationSettingsUpdate,
    WidgetCodeResponse
)
from app.models.hotel import Hotel

router = APIRouter(prefix="/integration", tags=["Integration"])


def hash_api_key(key: str) -> str:
    """Hash API key for secure storage"""
    return hashlib.sha256(key.encode()).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """
    Generate API key with prefix and hash.
    Returns: (full_key, prefix, hash)
    """
    # Generate random key
    random_part = secrets.token_urlsafe(32)
    full_key = f"sk_live_{random_part}"
    
    # Get prefix (first 12 chars for display)
    prefix = full_key[:12] + "..."
    
    # Hash for storage
    key_hash = hash_api_key(full_key)
    
    return full_key, prefix, key_hash


@router.get("/settings", response_model=IntegrationSettingsRead)
async def get_integration_settings(
    current_user: CurrentUser,
    session: DbSession
):
    """Get integration settings for current hotel"""
    query = select(IntegrationSettings).where(
        IntegrationSettings.hotel_id == current_user.hotel_id
    )
    result = await session.execute(query)
    settings = result.scalar_one_or_none()
    
    # Create default settings if not exists
    if not settings:
        settings = IntegrationSettings(hotel_id=current_user.hotel_id)
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    
    return settings


@router.put("/settings", response_model=IntegrationSettingsRead)
async def update_integration_settings(
    settings_update: IntegrationSettingsUpdate,
    current_user: CurrentUser,
    session: DbSession
):
    """Update integration settings"""
    query = select(IntegrationSettings).where(
        IntegrationSettings.hotel_id == current_user.hotel_id
    )
    result = await session.execute(query)
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create new settings
        settings = IntegrationSettings(
            hotel_id=current_user.hotel_id,
            **settings_update.model_dump(exclude_unset=True)
        )
        session.add(settings)
    else:
        # Update existing
        for key, value in settings_update.model_dump(exclude_unset=True).items():
            setattr(settings, key, value)
        settings.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(settings)
    return settings


@router.get("/api-keys", response_model=List[APIKeyRead])
async def list_api_keys(
    current_user: CurrentUser,
    session: DbSession
):
    """List all API keys for current hotel"""
    query = select(APIKey).where(
        APIKey.hotel_id == current_user.hotel_id
    ).order_by(APIKey.created_at.desc())
    
    result = await session.execute(query)
    keys = result.scalars().all()
    return keys


@router.post("/api-keys", response_model=APIKeyWithSecret)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: CurrentUser,
    session: DbSession
):
    """
    Create a new API key.
    ⚠️ The secret key is only shown ONCE during creation!
    """
    # Generate key
    full_key, prefix, key_hash = generate_api_key()
    
    # Calculate expiry
    expires_at = None
    if key_data.expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=key_data.expires_in_days)
    
    # Create API key record
    api_key = APIKey(
        hotel_id=current_user.hotel_id,
        name=key_data.name,
        key_prefix=prefix,
        key_hash=key_hash,
        scopes=key_data.scopes,
        expires_at=expires_at
    )
    
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    
    # Return with secret (only time it's shown)
    return APIKeyWithSecret(
        **api_key.model_dump(),
        secret_key=full_key
    )


@router.delete("/api-keys/{key_id}")
async def delete_api_key(
    key_id: str,
    current_user: CurrentUser,
    session: DbSession
):
    """Delete (revoke) an API key"""
    query = select(APIKey).where(
        APIKey.id == key_id,
        APIKey.hotel_id == current_user.hotel_id
    )
    result = await session.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    await session.delete(api_key)
    await session.commit()
    
    return {"message": "API key deleted successfully"}


@router.put("/api-keys/{key_id}/toggle")
async def toggle_api_key(
    key_id: str,
    current_user: CurrentUser,
    session: DbSession
):
    """Enable or disable an API key"""
    query = select(APIKey).where(
        APIKey.id == key_id,
        APIKey.hotel_id == current_user.hotel_id
    )
    result = await session.execute(query)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = not api_key.is_active
    await session.commit()
    await session.refresh(api_key)
    
    return api_key


@router.get("/widget-code", response_model=WidgetCodeResponse)
async def get_widget_code(
    current_user: CurrentUser,
    session: DbSession
):
    """
    Get embeddable widget code for hotel website.
    Returns HTML, JS, and CSS code snippets.
    """
    # Get hotel details
    hotel = await session.get(Hotel, current_user.hotel_id)
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    
    # Get integration settings
    settings_query = select(IntegrationSettings).where(
        IntegrationSettings.hotel_id == current_user.hotel_id
    )
    settings_result = await session.execute(settings_query)
    settings = settings_result.scalar_one_or_none()
    
    if not settings:
        settings = IntegrationSettings(hotel_id=current_user.hotel_id)
    
    # Use Base URLs from config
    from app.core.config import get_settings
    config = get_settings()
    
    api_url = config.API_URL
    frontend_url = config.FRONTEND_URL

    hotel_slug = hotel.slug
    
    html_code = f'''<!-- Hotelier Hub Booking Widget -->
<div id="hotelier-booking-widget" 
     data-hotel-slug="{hotel_slug}"
     data-theme="{settings.widget_theme}"
     data-color="{settings.widget_primary_color}">
</div>'''
    
    javascript_code = f'''<script>
  (function() {{
    var script = document.createElement('script');
    script.src = '{frontend_url}/widget.js';
    script.async = true;
    script.onload = function() {{
      HotelierWidget.init({{
        hotelSlug: '{hotel_slug}',
        primaryColor: '{settings.widget_primary_color}',
        theme: '{settings.widget_theme}',
        apiUrl: '{api_url}',
        frontendUrl: '{frontend_url}'
      }});
    }};
    document.head.appendChild(script);
  }})();
</script>'''
    
    css_code = f'''<style>
  #hotelier-booking-widget {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  }}
  /* Widget will load its own styles */
</style>'''
    
    instructions = f'''
# Integration Instructions

## Step 1: Add the HTML
Paste this code where you want the booking widget to appear on your website:

{html_code}

## Step 2: Add the JavaScript
Add this script tag before the closing </body> tag:

{javascript_code}

## Step 3: (Optional) Verify Domain
Ensure your website domain (e.g., www.lagoonaresort.com) is added to the "Allowed Domains" list in Settings.

## Direct Booking Link:
You can also link directly to your booking page:
{frontend_url}/book/{hotel_slug}/rooms

## Need Help?
Contact support or check our documentation for advanced customization options.
'''
    
    return WidgetCodeResponse(
        html_code=html_code,
        javascript_code=javascript_code,
        css_code=css_code,
        instructions=instructions
    )


@router.get("/webhook-test")
async def test_webhook(
    current_user: CurrentUser,
    session: DbSession
):
    """
    Test webhook configuration by sending a test event.
    """
    settings_query = select(IntegrationSettings).where(
        IntegrationSettings.hotel_id == current_user.hotel_id
    )
    result = await session.execute(settings_query)
    settings = result.scalar_one_or_none()
    
    if not settings or not settings.webhook_url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Webhook URL not configured"
        )
    
    # TODO: Implement actual webhook sending
    # For now, just return success
    return {
        "message": "Webhook test initiated",
        "webhook_url": settings.webhook_url,
        "note": "Check your webhook endpoint for the test event"
    }
