# Example JSON Uploads and Expected Responses

## Example 1: SQL Classification

### Input File: `sql_example.json`

**Why SQL?**
- Low nesting depth (max 2 levels)
- Contains flat objects representing entities (users, blogs, comments)
- Consistent schema across objects
- Represents relational data with foreign keys (author_id, blog_id)
- **Classification Score**: ~0.25 (< 0.5 threshold) → **SQL**

```json
{
  "users": {
    "id": "usr_67f8a1c9",
    "username": "priya_sharma",
    "email": "priya.sharma@example.in",
    "age": 28,
    "created_at": "2025-11-16T06:27:15.342Z"
  },
  "blogs": {
    "id": "blog_9d2e4f7b",
    "title": "Exploring Mumbai's Hidden Cafes",
    "content": "Today I discovered amazing cafes in Mumbai...",
    "author_id": "usr_67f8a1c9",
    "published_at": "2025-11-16T06:30:00.000Z",
    "created_at": "2025-11-16T06:27:45.112Z"
  },
  "comments": {
    "id": "cmt_3b1k9m4p",
    "blog_id": "blog_9d2e4f7b",
    "author_id": "usr_67f8a1c9",
    "content": "The filter coffee at Cafe Iris is a must-try!",
    "created_at": "2025-11-16T06:35:22.789Z"
  }
}
```

### Expected Response:

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
            "name": "username",
            "type": "string",
            "required": true
          },
          {
            "name": "email",
            "type": "email",
            "required": true
          },
          {
            "name": "age",
            "type": "integer",
            "required": true
          },
          {
            "name": "created_at",
            "type": "datetime",
            "required": true
          }
        ],
        "rows_inserted": 1
      },
      {
        "table_name": "blogs",
        "fields": [
          {
            "name": "id",
            "type": "string",
            "required": true
          },
          {
            "name": "title",
            "type": "string",
            "required": true
          },
          {
            "name": "content",
            "type": "string",
            "required": true
          },
          {
            "name": "author_id",
            "type": "string",
            "required": true
          },
          {
            "name": "published_at",
            "type": "datetime",
            "required": true
          },
          {
            "name": "created_at",
            "type": "datetime",
            "required": true
          }
        ],
        "rows_inserted": 1
      },
      {
        "table_name": "comments",
        "fields": [
          {
            "name": "id",
            "type": "string",
            "required": true
          },
          {
            "name": "blog_id",
            "type": "string",
            "required": true
          },
          {
            "name": "author_id",
            "type": "string",
            "required": true
          },
          {
            "name": "content",
            "type": "string",
            "required": true
          },
          {
            "name": "created_at",
            "type": "datetime",
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
        "query": "INSERT INTO \"users\" (\"id\", \"username\", \"email\", \"age\", \"created_at\") VALUES (%s, %s, %s, %s, %s)",
        "sample_values": [
          "usr_67f8a1c9",
          "priya_sharma",
          "priya.sharma@example.in",
          28,
          "2025-11-16T06:27:15.342Z"
        ]
      },
      {
        "type": "SELECT",
        "table": "users",
        "query": "SELECT \"id\", \"username\", \"email\", \"age\", \"created_at\" FROM \"users\" LIMIT 10"
      },
      {
        "type": "UPDATE",
        "table": "users",
        "query": "UPDATE \"users\" SET \"username\" = %s, \"email\" = %s WHERE \"id\" = %s",
        "sample_values": [
          "priya_sharma",
          "priya.sharma@example.in",
          "usr_67f8a1c9"
        ]
      }
    ],
    "status": "success"
  }
}
```

### What Happens Behind the Scenes:

1. **Classification**: 
   - Depth score: 0 (max depth = 2, below threshold of 3)
   - Array score: 0 (no arrays of objects)
   - Consistency score: 0 (consistent schema)
   - **Total**: 0 → **SQL**

2. **Tables Created**:
```sql
CREATE TABLE "users" (
    "id" VARCHAR(255) PRIMARY KEY,
    "username" VARCHAR(255) NOT NULL,
    "email" VARCHAR(255) NOT NULL,
    "age" INTEGER NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL
);

CREATE TABLE "blogs" (
    "id" VARCHAR(255) PRIMARY KEY,
    "title" VARCHAR(255) NOT NULL,
    "content" TEXT NOT NULL,
    "author_id" VARCHAR(255) NOT NULL,
    "published_at" TIMESTAMPTZ NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    FOREIGN KEY ("author_id") REFERENCES "users"("id")
);

CREATE TABLE "comments" (
    "id" VARCHAR(255) PRIMARY KEY,
    "blog_id" VARCHAR(255) NOT NULL,
    "author_id" VARCHAR(255) NOT NULL,
    "content" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    FOREIGN KEY ("blog_id") REFERENCES "blogs"("id"),
    FOREIGN KEY ("author_id") REFERENCES "users"("id")
);
```

3. **Data Inserted**: 1 row in each table
4. **Queries Generated**: INSERT, SELECT, UPDATE for first table

---

## Example 2: NoSQL Classification

### Input File: `nosql_example.json`

**Why NoSQL?**
- Deep nesting (7+ levels: user.profile.personal.contact.address.city)
- Heavily nested objects (profile, preferences, notifications, etc.)
- Arrays with nested objects (orders with items, specifications, payment, shipping)
- Inconsistent structure depth across branches
- Document-oriented structure not easily normalized
- **Classification Score**: ~0.75 (>= 0.5 threshold) → **NoSQL**

```json
{
  "user": {
    "profile": {
      "personal": {
        "name": "Alice Johnson",
        "age": 30,
        "contact": {
          "email": "alice@example.com",
          "phone": {
            "primary": "123-456-7890",
            "secondary": "098-765-4321"
          },
          "address": {
            "street": "123 Main St",
            "city": "Mumbai",
            "state": "Maharashtra",
            "country": "India",
            "postal_code": "400001"
          }
        }
      },
      "preferences": {
        "theme": "dark",
        "language": "en",
        "notifications": {
          "email": true,
          "sms": false,
          "push": true
        }
      }
    },
    "activity": {
      "last_login": "2025-11-16T10:30:00Z",
      "session_count": 42,
      "devices": [
        {
          "type": "mobile",
          "os": "iOS",
          "version": "17.1",
          "last_used": "2025-11-16T10:30:00Z"
        },
        {
          "type": "desktop",
          "os": "macOS",
          "version": "14.1",
          "last_used": "2025-11-15T14:20:00Z"
        }
      ]
    }
  },
  "orders": [...],
  "metadata": {...}
}
```

### Expected Response:

**Note**: Collection name is based on `user_id` parameter. If you upload with `user_id=alice_123`, the collection will be named `alice_123`.

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
          },
          {
            "name": "metadata",
            "type": "object",
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
          "user": {
            "profile": {
              "personal": {
                "name": "Alice Johnson",
                "age": 30,
                "contact": {
                  "email": "alice@example.com",
                  "phone": {
                    "primary": "123-456-7890",
                    "secondary": "098-765-4321"
                  },
                  "address": {
                    "street": "123 Main St",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India",
                    "postal_code": "400001"
                  }
                }
              },
              "preferences": {
                "theme": "dark",
                "language": "en",
                "notifications": {
                  "email": true,
                  "sms": false,
                  "push": true
                }
              }
            },
            "activity": {
              "last_login": "2025-11-16T10:30:00Z",
              "session_count": 42,
              "devices": [
                {
                  "type": "mobile",
                  "os": "iOS",
                  "version": "17.1",
                  "last_used": "2025-11-16T10:30:00Z"
                },
                {
                  "type": "desktop",
                  "os": "macOS",
                  "version": "14.1",
                  "last_used": "2025-11-15T14:20:00Z"
                }
              ]
            }
          },
          "orders": [
            {
              "id": "550e8400-e29b-41d4-a716-446655440000",
              "items": [
                {
                  "product_id": "prod_123",
                  "name": "Laptop",
                  "quantity": 1,
                  "price": 75000.00,
                  "specifications": {
                    "brand": "Apple",
                    "model": "MacBook Pro",
                    "ram": "16GB",
                    "storage": "512GB SSD"
                  }
                },
                {
                  "product_id": "prod_456",
                  "name": "Mouse",
                  "quantity": 2,
                  "price": 1500.00
                }
              ],
              "total": 78000.00,
              "status": "delivered",
              "payment": {
                "method": "credit_card",
                "transaction_id": "txn_abc123",
                "status": "completed"
              },
              "shipping": {
                "address": {
                  "street": "456 Oak Ave",
                  "city": "Pune",
                  "state": "Maharashtra",
                  "country": "India"
                },
                "tracking_number": "TRACK123456",
                "delivered_at": "2025-11-10T15:30:00Z"
              }
            }
          ],
          "metadata": {
            "account_created": "2023-01-15T08:00:00Z",
            "account_type": "premium",
            "subscription": {
              "plan": "annual",
              "price": 9999.00,
              "next_billing": "2026-01-15T00:00:00Z",
              "features": ["priority_support", "unlimited_storage", "advanced_analytics"]
            }
          }
        }
      },
      {
        "type": "find",
        "collection": "alice_123",
        "operation": "db.alice_123.find(...)",
        "filter": {
          "user": {
            "profile": {
              "personal": {
                "name": "Alice Johnson"
              }
            }
          }
        }
      },
      {
        "type": "updateOne",
        "collection": "alice_123",
        "operation": "db.alice_123.updateOne(...)",
        "filter": {
          "user": {
            "profile": {
              "personal": {
                "name": "Alice Johnson"
              }
            }
          }
        },
        "update": {
          "$set": {
            "user": {
              "profile": {
                "personal": {
                  "name": "Alice Johnson",
                  "age": 30
                }
              }
            }
          }
        }
      }
    ],
    "status": "success"
  }
}
```

### What Happens Behind the Scenes:

1. **Classification**:
   - Depth score: 0.4 (max depth = 7, exceeds threshold of 3)
   - Array score: 0.35 (contains arrays with objects: devices, orders, items)
   - Consistency score: 0 (but overall score already high)
   - **Total**: 0.75 → **NoSQL**

2. **Collection Created** (named after user_id, e.g., "alice_123"):
```javascript
db.createCollection("alice_123", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["user", "orders", "metadata"],
      properties: {
        user: { bsonType: "object" },
        orders: { bsonType: "array" },
        metadata: { bsonType: "object" }
      }
    }
  }
});
```

3. **Document Inserted**: 1 complete document with nested structure preserved per user
4. **Queries Generated**: insertOne, find, updateOne for the user's collection
5. **Collection Isolation**: Each user gets their own collection (e.g., alice_123, bob_456, etc.)

---

## How to Test

### Using curl:

**SQL Example:**
```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@examples/sql_example.json" \
  -F "user_id=test_user"
```

**NoSQL Example (with user_id):**
```bash
# Collection will be named "alice_123"
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@examples/nosql_example.json" \
  -F "user_id=alice_123"
```

**NoSQL Example (without user_id):**
```bash
# Collection will be named "anonymous" (default)
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@examples/nosql_example.json"
```

### Using Python:

```python
import requests

# SQL Example
with open('examples/sql_example.json', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/upload',
        files={'file': f},
        data={'user_id': 'test_user'}
    )
    print("SQL Response:", response.json())

# NoSQL Example with user_id (collection will be named "alice_123")
with open('examples/nosql_example.json', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/v1/upload',
        files={'file': f},
        data={'user_id': 'alice_123'}
    )
    print("NoSQL Response:", response.json())
```

---

## Key Differences in Responses

| Aspect | SQL | NoSQL |
|--------|-----|-------|
| **schema_type** | `"sql"` | `"nosql"` |
| **Container** | `tables` array | `collections` array |
| **Structure** | Multiple tables with flat fields | Single collection with nested structure |
| **Queries** | INSERT, SELECT, UPDATE with SQL syntax | insertOne, find, updateOne with MongoDB syntax |
| **Values** | Parameterized (%s) with sample_values | Direct document/filter objects |
| **Normalization** | Entities separated into tables | Document kept nested |

---

## Classification Thresholds

The system uses these weights in the classification algorithm:

- **Depth Score**: 0.4 weight (triggered when depth > 3)
- **Array Score**: 0.35 weight (triggered when arrays contain objects)
- **Consistency Score**: 0.25 weight (triggered when schema is inconsistent)

**Decision**:
- Score < 0.5 → **SQL** (PostgreSQL)
- Score >= 0.5 → **NoSQL** (MongoDB)
