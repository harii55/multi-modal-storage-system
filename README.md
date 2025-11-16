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

### 4. **Schema Evolution**
- **ALTER TABLE**: Adds new columns when compatible
- **Versioning**: Creates new versioned tables (e.g., `users_v2`) when incompatible
- **MongoDB Validators**: Automatically applies or updates collection validators

### 5. **Media Storage**
- Uploads non-JSON files to MinIO object storage
- Returns presigned URLs for secure access
- Content-type detection and metadata tracking

### 6. **User Management**
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
```

#### Response for JSON (SQL)
```json
{
  "type": "json",
  "result": {
    "schema_type": "sql",
    "sql": {
      "users": "CREATE TABLE IF NOT EXISTS \"users\" (...)"
    },
    "actions": [
      {
        "table": "users",
        "action": "create",
        "ddl": "CREATE TABLE..."
      }
    ],
    "status": "success"
  }
}
```

#### Response for JSON (NoSQL)
```json
{
  "type": "json",
  "result": {
    "schema_type": "nosql",
    "nosql": {
      "root": {
        "$jsonSchema": {
          "bsonType": "object",
          "properties": {...}
        }
      }
    },
    "actions": [...],
    "status": "success"
  }
}
```

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
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@test_sql.json"
```

**test_sql.json**:
```json
[
  {"id": 1, "name": "John", "age": 25},
  {"id": 2, "name": "Jane", "age": 30}
]
```

### Test NoSQL Classification
```bash
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@test_nosql.json"
```

**test_nosql.json**:
```json
{
  "users": [
    {"id": 1, "name": "John", "profile": {"age": 25}},
    {"id": 2, "name": "Jane", "details": {"age": 30}, "extra": "field"}
  ]
}
```

### Test Media Upload
```bash
curl -X POST http://localhost:8000/v1/upload \
  -F "file=@image.png"
```

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
│   │   └── upload.py            # File upload endpoint
│   ├── db/
│   │   ├── postgres/
│   │   │   ├── client.py        # PostgreSQL client
│   │   │   └── base_schema.sql  # Base schema
│   │   ├── mongo/
│   │   │   └── client.py        # MongoDB client
│   │   └── minio/
│   │       └── client.py        # MinIO client
│   ├── services/
│   │   ├── json_service/
│   │   │   ├── processor.py     # Main JSON processor with YOUR algorithm
│   │   │   ├── infer_type/      # Type inference
│   │   │   ├── entity_extractor/ # Entity detection
│   │   │   ├── normalizer/       # Schema normalization
│   │   │   ├── table_generator/  # SQL/NoSQL generators
│   │   │   └── schema_checker/   # Schema comparison & versioning
│   │   └── media_service/
│   │       └── processor.py     # Media processing
│   └── utils/
│       └── detectors/
│           └── type_detector.py # JSON vs Media detection
├── main.py
├── requirements.txt
└── README.md
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

## 🎉 What Makes This Special

1. **Your Algorithm is Preserved**: The exact SQL/NoSQL classification logic you provided is intact
2. **Best of Both Worlds**: Fast classification + Comprehensive schema generation
3. **Production-Ready**: Handles schema evolution, versioning, and ALTER statements
4. **Type-Smart**: Detects UUIDs, datetimes, emails, and URLs automatically
5. **Database-Agnostic**: Generates schemas for both SQL and NoSQL simultaneously

## 🚧 Next Steps

- Add authentication/authorization
- Implement async database operations
- Add comprehensive test suite
- Support for more complex relationships (foreign keys)
- Add data validation before insertion
- Support for batch uploads
- Add logging and monitoring

## 📝 License

MIT

## 👤 Author

**Hariny Patel**

---

**Built with ❤️ using FastAPI, PostgreSQL, MongoDB, and MinIO**