from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
import os
import uuid
import io
import aiofiles
# Trigger reload
from typing import List
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from app.api.deps import get_current_active_user

router = APIRouter(prefix="/upload", tags=["Upload"])

# Get the directory where this file is located (backend/app/api/v1/)
# Go up to backend directory and then to static/uploads
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = BACKEND_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 5MB Limit
MAX_FILE_SIZE = 5 * 1024 * 1024

@router.get("", response_model=dict)
async def test_upload_route():
    return {"message": "Upload route is active"}

import requests
from app.core.config import get_settings

settings = get_settings()

@router.post("", response_model=dict)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user = Depends(get_current_active_user)
):
    try:
        # 1. Read file content
        contents = await file.read()
        
        # 2. Check file size
        if len(contents) > MAX_FILE_SIZE:
             raise HTTPException(status_code=413, detail="File too large. Maximum size is 5MB.")

        # 3. Verify it's a real image using Pillow
        try:
            image = Image.open(io.BytesIO(contents))
            image.verify() 
            image = Image.open(io.BytesIO(contents))
            img_format = image.format
        except (UnidentifiedImageError, Exception):
            raise HTTPException(status_code=400, detail="Invalid image file or format not supported.")

        # 4. Generate unique filename
        ext = os.path.splitext(file.filename)[1].lower() if file.filename else ".jpg"
        if not ext or ext == ".":
            ext = f".{img_format.lower()}" if img_format else ".jpg"
            
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        # 5. Upload to Supabase Storage
        if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
            raise HTTPException(status_code=500, detail="Supabase configuration missing in backend.")

        # Supabase Storage Details
        bucket_name = "hotel-assets"
        storage_url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket_name}/{unique_filename}"
        
        headers = {
            "apikey": settings.SUPABASE_ANON_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_ANON_KEY}",
            "Content-Type": file.content_type or "image/jpeg"
        }

        # Sync request for simplicity in this endpoint
        response = requests.post(storage_url, headers=headers, data=contents)
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get("message", "Storage upload failed")
            if "Bucket not found" in error_msg:
                error_msg = "Storage Bucket 'hotel-assets' not found. Please create a public bucket named 'hotel-assets' in your Supabase dashboard."
            raise HTTPException(status_code=response.status_code, detail=error_msg)

        # 6. Construct Public URL
        # Format: {URL}/storage/v1/object/public/{bucket}/{file}
        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{unique_filename}"
        
        return {"url": public_url}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

