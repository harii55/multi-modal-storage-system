from typing import Dict, Any, List
from app.db.minio.client import MinioClient
import os
import io
import uuid
import zipfile
import tempfile
import string

try:
    import magic
except ImportError:
    magic = None

class MediaProcessor:
    # Extension sets for categorization
    IMAGE_EXTS = {"jpg", "jpeg", "jpe", "png", "webp", "svg", "heic", "heif", "raw", "cr2", "nef", "arw", "dng", "rw2", "raf", "orf", "gif", "bmp", "tiff", "tif"}
    DOC_EXTS = {"pdf", "docx", "doc", "xlsx", "xls", "pptx", "ppt", "txt", "md", "markdown", "rtf", "srt", "odt", "ods", "odp", "csv"}
    AUDIO_EXTS = {"wav", "mp3", "m4a", "aac", "flac", "ogg", "oga", "opus", "amr", "wma", "aiff"}
    VIDEO_EXTS = {"mp4", "mov", "m4v", "webm", "mkv", "avi", "mpg", "mpeg", "flv", "3gp", "wmv"}
    ARCHIVE_EXTS = {"zip", "tar", "gz", "tgz", "7z", "rar"}
    
    def __init__(self):
        self.minio = MinioClient()
        self.bucket = os.getenv('MINIO_BUCKET', 'user-uploads')
        self.default_url_expires = int(os.getenv('DEFAULT_URL_EXPIRES', '3600'))
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure the bucket exists"""
        try:
            self.minio.ensure_bucket(self.bucket)
        except Exception as e:
            print(f"Warning: Could not ensure bucket: {e}")
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename to prevent path traversal and issues"""
        name = os.path.basename(name or "")
        name = name.replace(" ", "_")
        allowed = "-_.() %s%s" % (string.ascii_letters, string.digits)
        return "".join(c for c in name if c in allowed)[:240] or "file"
    
    def _get_extension(self, filename: str) -> str:
        """Extract file extension"""
        return os.path.splitext(filename or "")[1].lower().lstrip(".")
    
    def _detect_type_and_folder(self, file_bytes: bytes, filename: str) -> tuple:
        """
        Detect MIME type and determine folder category
        Returns: (mime_type, folder_category, extension)
        """
        mime = None
        
        # Try python-magic for accurate detection
        if magic:
            try:
                mime = magic.from_buffer(file_bytes, mime=True)
            except Exception:
                pass
        
        ext = self._get_extension(filename or "")
        
        # MIME-based detection (most accurate)
        if mime:
            if mime.startswith("image/"):
                return mime, "images", ext
            if mime.startswith("audio/"):
                return mime, "audio", ext
            if mime.startswith("video/"):
                return mime, "video", ext
            if mime == "application/pdf":
                return mime, "documents", ext
            if mime.startswith("text/") or mime in ("application/json", "application/xml"):
                return mime, "documents", ext
            if "officedocument" in (mime or "") or "word" in (mime or ""):
                return mime, "documents", ext
        
        # Extension-based fallback
        if ext in self.IMAGE_EXTS:
            guessed = f"image/{'jpeg' if ext in ('jpg', 'jpeg', 'jpe') else ext}"
            return guessed, "images", ext
        
        if ext in self.AUDIO_EXTS:
            guessed = f"audio/{ext}"
            return guessed, "audio", ext
        
        if ext in self.VIDEO_EXTS:
            guessed = f"video/{ext}"
            return guessed, "video", ext
        
        if ext in self.DOC_EXTS:
            mime_map = {
                "pdf": "application/pdf",
                "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "doc": "application/msword",
                "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "xls": "application/vnd.ms-excel",
                "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "txt": "text/plain",
                "md": "text/markdown",
                "csv": "text/csv",
            }
            guessed = mime_map.get(ext, "application/octet-stream")
            return guessed, "documents", ext
        
        if ext in self.ARCHIVE_EXTS:
            guessed = "application/zip" if ext == "zip" else "application/x-compressed"
            return guessed, "archives", ext
        
        return (mime or "application/octet-stream"), "others", ext
    
    def _upload_single_file(self, user_id: str, filename: str, file_bytes: bytes) -> Dict[str, Any]:
        """Upload a single file to MinIO in organized folder structure"""
        mime_type, folder, ext = self._detect_type_and_folder(file_bytes, filename)
        
        # Generate unique ID and sanitize filename
        uid = str(uuid.uuid4())
        safe_name = self._sanitize_filename(filename)
        
        # Construct object key: users/{user_id}/{category}/{uuid}_{filename}
        object_key = f"users/{user_id}/{folder}/{uid}_{safe_name}"
        
        # Upload to MinIO
        self.minio.put_object(self.bucket, object_key, file_bytes, mime_type)
        
        # Generate presigned URL
        url = self.minio.presigned_get(self.bucket, object_key, expiry=self.default_url_expires)
        
        return {
            'key': object_key,
            'url': url,
            'mime': mime_type,
            'folder': folder,
            'size': len(file_bytes),
            'original_filename': filename
        }
    
    def _process_zip_archive(self, user_id: str, file_bytes: bytes) -> List[Dict[str, Any]]:
        """Extract and upload all files from a ZIP archive"""
        uploaded_files = []
        
        with tempfile.TemporaryDirectory() as td:
            zip_path = os.path.join(td, "incoming.zip")
            
            # Write zip to temp file
            with open(zip_path, "wb") as f:
                f.write(file_bytes)
            
            # Extract and process each file
            with zipfile.ZipFile(zip_path, 'r') as z:
                for zi in z.infolist():
                    if zi.is_dir():
                        continue
                    
                    # Read entry
                    with z.open(zi) as entry:
                        entry_bytes = entry.read()
                        entry_result = self._upload_single_file(user_id, zi.filename, entry_bytes)
                        uploaded_files.append(entry_result)
        
        return uploaded_files
    
    def process(self, filename: str, file_bytes: bytes, user_id: str = 'anonymous') -> Dict[str, Any]:
        """
        Process non-JSON files (media, documents, archives, etc.)
        Organizes files by user and category, extracts archives
        
        Args:
            filename: Original filename
            file_bytes: File content as bytes
            user_id: User identifier for folder organization
        
        Returns:
            Dict with upload results including URLs and metadata
        """
        try:
            mime_type, folder, ext = self._detect_type_and_folder(file_bytes, filename)
            
            # Handle ZIP archives - extract and upload each file
            if ext == "zip" or mime_type == "application/zip":
                uploaded_files = self._process_zip_archive(user_id, file_bytes)
                return {
                    'type': 'archive',
                    'status': 'extracted_and_uploaded',
                    'archive_name': filename,
                    'files_count': len(uploaded_files),
                    'files': uploaded_files,
                    'message': f'ZIP archive extracted: {len(uploaded_files)} files uploaded'
                }
            
            # Handle regular files
            result = self._upload_single_file(user_id, filename, file_bytes)
            
            return {
                'type': 'file',
                'status': 'uploaded',
                'file': result,
                'message': 'File uploaded successfully'
            }
        
        except zipfile.BadZipFile:
            return {
                'status': 'error',
                'message': 'Invalid ZIP file',
                'error': 'BadZipFile'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Upload failed: {str(e)}',
                'error': type(e).__name__
            }