
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.detectors.type_detector import TypeDetector
from app.services.json_service.processor import JsonProcessor
from app.services.media_service.processor import MediaProcessor

router = APIRouter()

detector = TypeDetector()
json_processor = JsonProcessor()
media_processor = MediaProcessor()

@router.post("/upload")
async def upload_handler(file: UploadFile = File(...)):
    file_bytes = await file.read()

    # Detect type
    detected_type = detector.detect(file.filename, file_bytes)

    if detected_type == "json":
        result = json_processor.process(file_bytes)
        return {"type": "json", "result": result}

    elif detected_type == "media":
        result = media_processor.process(file.filename, file_bytes)
        return {"type": "media", "result": result}

    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")