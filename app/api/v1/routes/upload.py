
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
from app.utils.detectors.type_detector import TypeDetector
from app.services.json_service.processor import JsonProcessor
from app.services.media_service.processor import MediaProcessor

router = APIRouter()

detector = TypeDetector()
json_processor = JsonProcessor()
media_processor = MediaProcessor()

@router.post("/upload")
async def upload_handler(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None)
):
    """
    Upload endpoint that handles both JSON and media files
    
    Args:
        file: The file to upload
        user_id: Optional user identifier for organizing media files
    """
    # Default user_id if not provided
    if not user_id:
        user_id = 'anonymous'
    
    file_bytes = await file.read()

    # Detect type
    detected_type = detector.detect(file.filename, file_bytes)

    if detected_type == "json":
        result = json_processor.process(file_bytes, user_id=user_id)
        return {"type": "json", "result": result}

    elif detected_type == "media":
        result = media_processor.process(file.filename, file_bytes, user_id=user_id)
        return {"type": "media", "result": result}

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")