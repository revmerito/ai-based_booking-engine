from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Depends
import os
import uuid
import io
import aiofiles
import logging
from typing import List
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from app.core.supabase import get_supabase
from app.api.deps import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/upload", tags=["Upload"])

# SECURITY: File upload constraints
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/webp", "image/gif", "application/pdf"
}

@router.post("", response_model=dict)
async def upload_file(
    file: UploadFile = File(...),
    current_user = Depends(get_current_active_user)
):
    try:
        # SECURITY: Validate filename exists
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # SECURITY: Validate extension
        original_ext = os.path.splitext(file.filename)[1].lower()
        if original_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # 1. Read file content
        contents = await file.read()
        
        # 2. Check file size
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File too large")
        
        # 3. Choose bucket
        bucket_id = "reports" if original_ext == ".pdf" else "hotel-assets"
        
        # 4. Generate unique filename
        unique_filename = f"{uuid.uuid4()}{original_ext}"
        
        # 5. Upload to Supabase Storage
        supabase_client = get_supabase()
        response = supabase_client.storage.from_(bucket_id).upload(
            path=unique_filename,
            file=contents,
            file_options={"content-type": file.content_type}
        )
        
        # 6. Get Public URL (if public bucket)
        if bucket_id == "hotel-assets":
            url_res = supabase_client.storage.from_(bucket_id).get_public_url(unique_filename)
            return {"url": url_res}
        else:
            # For reports, returning just the path if it's private
            return {"url": unique_filename, "bucket": bucket_id}

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="File upload failed")


