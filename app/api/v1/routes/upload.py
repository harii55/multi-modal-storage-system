
from fastapi import APIRouter, UploadFile, File
router = APIRouter()

@router.post("/upload")
async def upload_handler(file: UploadFile = File(...)):
    # detection + pipeline will be added later
    return {"filename": file.filename}