# Testing Guide - Media Upload with Folder Organization

## 📁 Folder Structure

Your system now organizes files by:
1. **User ID**: Each user gets their own folder
2. **MIME Type Category**: Files are categorized into folders
   - `images/` - Images (jpg, png, gif, svg, etc.)
   - `documents/` - Documents (pdf, docx, txt, md, csv, etc.)
   - `audio/` - Audio files (mp3, wav, m4a, etc.)
   - `video/` - Videos (mp4, mov, webm, etc.)
   - `archives/` - Archives (zip, tar, etc.)
   - `others/` - Uncategorized files

## 🎯 MinIO Organization

```
user-uploads/
└── users/
    ├── {user_id_1}/
    │   ├── images/
    │   │   └── {uuid}_{filename}.png
    │   ├── documents/
    │   │   └── {uuid}_{filename}.pdf
    │   ├── audio/
    │   ├── video/
    │   └── archives/
    ├── {user_id_2}/
    │   └── ...
    └── anonymous/
        └── ...
```

## 🧪 Quick Test Commands

### 1. Upload Image with User ID
```bash
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@test_files/sample_files/test_image.png" \
  -F "user_id=usr_67f8a1c9"
```

**Expected Response:**
```json
{
  "type": "media",
  "result": {
    "type": "file",
    "status": "uploaded",
    "file": {
      "key": "users/usr_67f8a1c9/images/{uuid}_test_image.png",
      "url": "http://localhost:9000/...",
      "mime": "image/png",
      "folder": "images",
      "size": 12345,
      "original_filename": "test_image.png"
    }
  }
}
```

### 2. Upload Document
```bash
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@test_files/sample_files/document.pdf" \
  -F "user_id=usr_67f8a1c9"
```

### 3. Upload ZIP Archive (Auto-Extract)
```bash
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@test_files/sample_files/photos.zip" \
  -F "user_id=usr_67f8a1c9"
```

**Expected Response:**
```json
{
  "type": "media",
  "result": {
    "type": "archive",
    "status": "extracted_and_uploaded",
    "archive_name": "photos.zip",
    "files_count": 5,
    "files": [
      {
        "key": "users/usr_67f8a1c9/images/{uuid}_photo1.jpg",
        "url": "http://...",
        "mime": "image/jpeg",
        "folder": "images"
      },
      ...
    ]
  }
}
```

### 4. Upload Without User ID (Uses 'anonymous')
```bash
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@test_files/sample_files/test.txt"
```

## 🎬 Run Complete Test Suite

```bash
# Run the automated test script
./test_media_upload.sh
```

This will:
- ✅ Create test files (images, documents, archives)
- ✅ Upload with different user IDs
- ✅ Extract and categorize ZIP contents
- ✅ Verify folder organization

## 📊 Supported File Types

### Images
- **Extensions**: jpg, jpeg, png, gif, webp, svg, bmp, tiff, heic, raw
- **MIME Types**: image/*
- **Folder**: `users/{user_id}/images/`

### Documents
- **Extensions**: pdf, docx, doc, xlsx, xls, pptx, txt, md, csv, rtf
- **MIME Types**: application/pdf, text/*, officedocument types
- **Folder**: `users/{user_id}/documents/`

### Audio
- **Extensions**: mp3, wav, m4a, aac, flac, ogg, opus
- **MIME Types**: audio/*
- **Folder**: `users/{user_id}/audio/`

### Video
- **Extensions**: mp4, mov, webm, mkv, avi, mpg, flv
- **MIME Types**: video/*
- **Folder**: `users/{user_id}/video/`

### Archives
- **Extensions**: zip, tar, gz, 7z, rar
- **Behavior**: Auto-extracts ZIP files and categorizes contents
- **Folder**: Each extracted file goes to its appropriate category

## 🔍 Verify Uploads

### Check MinIO (Web UI)
1. Open: http://localhost:9001
2. Login: minioadmin / minioadmin123
3. Browse bucket: `user-uploads`
4. Navigate: `users/{your_user_id}/`

### Check via CLI
```bash
# List buckets
docker exec -it minio-test mc ls local

# List user folders
docker exec -it minio-test mc ls local/user-uploads/users/

# List user's images
docker exec -it minio-test mc ls local/user-uploads/users/usr_67f8a1c9/images/
```

## 🎯 Example Use Cases

### Use Case 1: User Profile Picture Upload
```bash
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@profile.jpg" \
  -F "user_id=usr_67f8a1c9"
```
**Result**: `users/usr_67f8a1c9/images/{uuid}_profile.jpg`

### Use Case 2: Batch Document Upload (ZIP)
Create a ZIP with multiple PDFs and upload:
```bash
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@documents.zip" \
  -F "user_id=usr_67f8a1c9"
```
**Result**: All PDFs extracted to `users/usr_67f8a1c9/documents/`

### Use Case 3: Mixed Media Archive
Upload a ZIP containing images, videos, and documents:
```bash
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@mixed_content.zip" \
  -F "user_id=usr_67f8a1c9"
```
**Result**: 
- Images → `users/usr_67f8a1c9/images/`
- Videos → `users/usr_67f8a1c9/video/`
- Docs → `users/usr_67f8a1c9/documents/`

## 🔧 Configuration

Set environment variables:
```bash
# MinIO Configuration
export MINIO_BUCKET=user-uploads
export DEFAULT_URL_EXPIRES=3600  # 1 hour

# In .env file
MINIO_HOST=localhost
MINIO_PORT=9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET=user-uploads
DEFAULT_URL_EXPIRES=3600
```

## 🎉 Features

1. ✅ **User-based Organization**: Each user has isolated folders
2. ✅ **MIME Type Detection**: Uses python-magic for accurate detection
3. ✅ **Extension Fallback**: Works even without python-magic
4. ✅ **ZIP Extraction**: Automatically extracts and categorizes ZIP contents
5. ✅ **Secure Filenames**: Sanitizes filenames to prevent path traversal
6. ✅ **Presigned URLs**: Returns temporary URLs for secure access
7. ✅ **UUID Prefixes**: Prevents filename collisions

## 🚨 Troubleshooting

### Issue: "python-magic not installed"
```bash
# Install python-magic
pip install python-magic

# On Ubuntu/Debian
sudo apt-get install libmagic1

# On macOS
brew install libmagic
```

### Issue: "MinIO connection failed"
```bash
# Check MinIO is running
docker ps | grep minio

# Start MinIO if not running
docker start minio-test
```

### Issue: "Bucket doesn't exist"
The system auto-creates buckets, but you can manually create:
```bash
docker exec -it minio-test mc mb local/user-uploads
```

## 📝 Testing Checklist

- [ ] Upload image → Check `images/` folder
- [ ] Upload PDF → Check `documents/` folder
- [ ] Upload MP3 → Check `audio/` folder
- [ ] Upload MP4 → Check `video/` folder
- [ ] Upload ZIP → Verify extraction and categorization
- [ ] Upload with user_id → Verify user folder created
- [ ] Upload without user_id → Verify `anonymous` folder used
- [ ] Download via presigned URL → Verify file accessible
- [ ] Upload same filename twice → Verify UUID prevents collision

---

**Ready to test?** Run: `./test_media_upload.sh` 🚀
