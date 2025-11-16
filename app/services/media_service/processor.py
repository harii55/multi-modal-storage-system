from typing import Dict, Any
from app.db.minio.client import MinioClient
import mimetypes
import os

class MediaProcessor:
    def __init__(self):
        self.minio = MinioClient()
        self.bucket = os.getenv('MINIO_BUCKET', 'uploads')
    
    def process(self, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """
        Process non-JSON files (media, documents, etc.)
        Upload to MinIO and return metadata with presigned URL
        """
        content_type, _ = mimetypes.guess_type(filename)
        content_type = content_type or 'application/octet-stream'
        
        object_name = filename
        
        # Upload to MinIO
        self.minio.put_object(self.bucket, object_name, file_bytes, content_type)
        
        # Generate presigned URL
        url = self.minio.presigned_get(self.bucket, object_name)
        
        return {
            'bucket': self.bucket,
            'object': object_name,
            'url': url,
            'content_type': content_type,
            'size': len(file_bytes),
            'status': 'uploaded',
            'message': 'Media file uploaded successfully'
        }