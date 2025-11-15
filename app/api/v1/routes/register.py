
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from uuid import uuid4
from datetime import datetime
from app.services.db_service.postgres.client import PostgresClient
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register_user(payload: RegisterRequest):
    db = PostgresClient()
    existing = db.fetch_one("SELECT * FROM users WHERE email_id=%s", (payload.email,))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pass = pwd_context.hash(payload.password)
    user_id = str(uuid4())
    created_at = datetime.utcnow()

    db.execute(
        "INSERT INTO users (user_id, email_id, hashed_pass, created_at) VALUES (%s, %s, %s, %s)",
        (user_id, payload.email, hashed_pass, created_at)
    )
    return {"status": "success", "user_id": user_id}
