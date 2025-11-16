# Multi-Modal Storage System

A FastAPI-based backend service that intelligently processes uploaded files, classifies JSON data as SQL or NoSQL, and automatically generates and applies database schemas.

## 🎯 Key Features

### 1. **Smart File Classification**
- Detects JSON vs media files
- Uses advanced type detection with MIME types and content analysis

### 2. **Intelligent SQL/NoSQL Classification Algorithm**
Your custom scoring-based algorithm classifies JSON data:
- **Depth Score (0.4 weight)**: Deep nesting (>3 levels) → NoSQL
- **Array Score (0.35 weight)**: Arrays of objects → SQL-like tabular data
- **Schema Consistency Score (0.25 weight)**: Inconsistent schemas → NoSQL
- **Threshold**: 0.5 - Total score >= 0.5 → NoSQL, else SQL

### 3. **Automatic Schema Generation**
- **SQL**: Generates PostgreSQL CREATE TABLE DDL with proper type mapping
- **NoSQL**: Generates MongoDB JSON Schema validators
- Semantic type detection: UUID, datetime, email, URL, etc.

### 4. **Query Generation**
- **SQL**: Auto-generates INSERT, SELECT, UPDATE queries with parameterized values
- **NoSQL**: Auto-generates insertOne, find, updateOne operations with sample documents
- Returns 1-3 sample queries per upload showing how to interact with created schemas
- Uses actual data from uploaded JSON as sample values

### 5. **User Isolation (NoSQL)**
- **Collection Per User**: Each user gets their own MongoDB collection (e.g., `alice_123`, `bob_456`)
- Pass `user_id` parameter to create user-specific collections
- Default collection name: `anonymous` (if no user_id provided)
- Complete data isolation between users

### 6. **Schema Evolution**
- **ALTER TABLE**: Adds new columns when compatible
- **Versioning**: Creates new versioned tables (e.g., `users_v2`) when incompatible
- **MongoDB Validators**: Automatically applies or updates collection validators

### 7. **Media Storage with Organization**
- Uploads non-JSON files to MinIO with folder organization
- **User-based folders**: `users/{user_id}/`
- **Category folders**: `images/`, `documents/`, `audio/`, `video/`, `archives/`
- **ZIP extraction**: Auto-extracts and categorizes each file individually
- Returns presigned URLs for secure access
- Content-type detection and metadata tracking

### 8. **User Management**
- Simple registration endpoint with bcrypt password hashing
- PostgreSQL-backed user storage

## 🏗️ Architecture

```
┌─────────────┐
│   Upload    │
│  Endpoint   │
└──────┬──────┘
       │
       ├─── JSON? ──→ TypeDetector
       │              └─→ JsonProcessor
       │                  ├─→ SQL/NoSQL Classification (YOUR ALGORITHM)
       │                  ├─→ Entity Detection
       │                  ├─→ Schema Inference
       │                  ├─→ SQL: Generate DDL → PostgreSQL
       │                  └─→ NoSQL: Generate Validators → MongoDB
       │
       └─── Media? ──→ MediaProcessor
                       └─→ MinIO Upload + Presigned URL
```

## 📦 Installation

### Prerequisites
- Python 3.9+
- PostgreSQL
- MongoDB
- MinIO

### Setup

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd multi-modal-storage-system
```

2. **Create virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
Create a `.env` file:
```env
# PostgreSQL
PG_HOST=localhost
PG_USER=postgres
PG_PASS=your_password
PG_DB=main

# MongoDB
MONGO_USER=admin
MONGO_PASS=your_password
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_DB=main

# MinIO
MINIO_HOST=localhost
MINIO_PORT=9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123
MINIO_BUCKET=uploads
```

5. **Run the application**
```bash
uvicorn main:app --reload --port 8000
```

## 🚀 API Endpoints

### Register User
```bash
POST /v1/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

### Upload File
```bash
POST /v1/upload
Content-Type: multipart/form-data

file: <your-file>
user_id: <optional-user-identifier>  # For media organization and NoSQL collections
```

**Parameters:**
- `file`: The file to upload (JSON or media)
- `user_id` (optional): 
  - For **media**: Organizes files in `users/{user_id}/` folders
  - For **NoSQL**: Uses as collection name (e.g., collection `alice_123`)
  - Default: `anonymous`

#### Response for JSON (SQL)
```json
{
  "type": "json",
  "result": {
    "schema_type": "sql",
    "tables": [
      {
        "table_name": "users",
        "fields": [
          {
            "name": "id",
            "type": "string",
            "required": true
          },
          {
            "name": "name",
            "type": "string",
            "required": true
          },
          {
            "name": "email",
            "type": "email",
            "required": true
          }
        ],
        "rows_inserted": 1
      }
    ],
    "queries": [
      {
        "type": "INSERT",
        "table": "users",
        "query": "INSERT INTO \"users\" (\"id\", \"name\", \"email\") VALUES (%s, %s, %s)",
        "sample_values": ["123", "John", "john@example.com"]
      },
      {
        "type": "SELECT",
        "table": "users",
        "query": "SELECT \"id\", \"name\", \"email\" FROM \"users\" LIMIT 10"
      },
      {
        "type": "UPDATE",
        "table": "users",
        "query": "UPDATE \"users\" SET \"name\" = %s WHERE \"id\" = %s",
        "sample_values": ["John", "123"]
      }
    ],
    "status": "success"
  }
}
```

**Note**: No database credentials are returned for security. Only schema metadata and sample queries. (For now)

#### Response for JSON (NoSQL)
```json
{
  "type": "json",
  "result": {
    "schema_type": "nosql",
    "collections": [
      {
        "collection_name": "alice_123",
        "fields": [
          {
            "name": "user",
            "type": "object",
            "required": true
          },
          {
            "name": "orders",
            "type": "array",
            "required": true
          }
        ],
        "documents_inserted": 1
      }
    ],
    "queries": [
      {
        "type": "insertOne",
        "collection": "alice_123",
        "operation": "db.alice_123.insertOne(...)",
        "document": {
          "user": { "name": "Alice", "age": 30 },
          "orders": [{"id": "550e8400", "total": 150.50}]
        }
      },
      {
        "type": "find",
        "collection": "alice_123",
        "operation": "db.alice_123.find(...)",
        "filter": { "user": { "name": "Alice" } }
      },
      {
        "type": "updateOne",
        "collection": "alice_123",
        "operation": "db.alice_123.updateOne(...)",
        "filter": { "user": { "name": "Alice" } },
        "update": { "$set": { "orders": [...] } }
      }
    ],
    "status": "success"
  }
}
```

**Note**: Collection name is based on `user_id` parameter. Each user gets their own collection.

#### Response for Media
```json
{
  "type": "media",
  "result": {
    "bucket": "uploads",
    "object": "image.png",
    "url": "http://localhost:9000/...",
    "content_type": "image/png",
    "size": 12345,
    "status": "uploaded"
  }
}
```

## 🧪 Testing

### Test SQL Classification
```bash
# Using example files
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@examples/sql_example.json" \
  -F "user_id=test_user"
```

**See**: `examples/sql_example.json` for a complete SQL example (users, blogs, comments)

### Test NoSQL Classification
```bash
# With user_id - creates collection named "alice_123"
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@examples/nosql_example.json" \
  -F "user_id=alice_123"

# Without user_id - creates collection named "anonymous"
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@examples/nosql_example.json"
```

**See**: `examples/nosql_example.json` for a complete NoSQL example (deep nesting, arrays, complex structure)

### Test Media Upload with User Organization
```bash
# Uploads to: users/john_doe/images/{uuid}_profile.jpg
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@profile.jpg" \
  -F "user_id=john_doe"

# Without user_id - uploads to: users/anonymous/images/{uuid}_profile.jpg
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@profile.jpg"
```

### Test ZIP Extraction
```bash
# Extracts all files and organizes by MIME type
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@archive.zip" \
  -F "user_id=john_doe"
```

**Result**: Files extracted to appropriate folders:
- `users/john_doe/images/` - All image files
- `users/john_doe/documents/` - All document files
- `users/john_doe/audio/` - All audio files
- etc.

## 📊 Classification Algorithm Details

Your algorithm uses three weighted scores:

### 1. Depth Score (0.4)
- Calculates maximum nesting depth
- Threshold: > 3 levels
- **Example**: `{"a": {"b": {"c": {"d": 1}}}}` → depth 4 → 0.4 points

### 2. Array Score (0.35)
- Detects arrays containing objects
- Suggests tabular/SQL-like structure
- **Example**: `[{"id": 1}, {"id": 2}]` → 0.35 points

### 3. Schema Consistency Score (0.25)
- Checks for inconsistent schemas in arrays
- Inconsistent keys suggest NoSQL
- **Example**: `[{"a": 1}, {"b": 2}]` → 0.25 points

**Total Score >= 0.5 → NoSQL, else SQL**

## 🗂️ Project Structure

```
multi-modal-storage-system/
├── app/
│   ├── api/v1/routes/
│   │   ├── register.py          # User registration
│   │   └── upload.py            # File upload endpoint (with user_id support)
│   ├── db/
│   │   ├── postgres/
│   │   │   ├── client.py        # PostgreSQL client
│   │   │   └── base_schema.sql  # Base schema
│   │   ├── mongo/
│   │   │   └── client.py        # MongoDB client
│   │   └── minio/
│   │       └── client.py        # MinIO client with presigned URLs
│   ├── services/
│   │   ├── json_service/
│   │   │   ├── processor.py     # Main JSON processor with YOUR algorithm
│   │   │   ├── query_generator.py # Query generation (INSERT, SELECT, UPDATE, etc.)
│   │   │   ├── infer_type/      # Type inference (UUID, datetime, email)
│   │   │   ├── entity_extractor/ # Entity detection
│   │   │   ├── normalizer/       # Schema normalization
│   │   │   ├── table_generator/  # SQL/NoSQL generators
│   │   │   └── schema_checker/   # Schema comparison & versioning
│   │   └── media_service/
│   │       └── processor.py     # Media processing (folder organization, ZIP extraction)
│   └── utils/
│       └── detectors/
│           └── type_detector.py # JSON vs Media detection
├── examples/
│   ├── sql_example.json         # Example SQL classification input
│   └── nosql_example.json       # Example NoSQL classification input
├── main.py
├── requirements.txt
├── README.md
├── EXAMPLES.md                   # Detailed examples with expected responses
└── RECENT_CHANGES.md             # Latest feature updates
```

## 🔧 Configuration

### Type Mapping (SQL)
- `integer` → `BIGINT`
- `number` → `DOUBLE PRECISION`
- `boolean` → `BOOLEAN`
- `string` → `TEXT`
- `datetime` → `TIMESTAMPTZ`
- `uuid` → `UUID`
- `object`/`array` → `JSONB`

### BSON Type Mapping (NoSQL)
- `integer` → `int`
- `number` → `double`
- `boolean` → `bool`
- `object`/`array` → `object`
- Default → `string`

## 👤 Author

**Hariny Patel**

---

**Built using FastAPI, PostgreSQL, MongoDB, and MinIO**
