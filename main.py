from fastapi import FastAPI
from app.api.v1.routes.register import router as register_router
from app.api.v1.routes.upload import router as upload_router

app = FastAPI()
app.include_router(register_router, prefix="/v1")
app.include_router(upload_router, prefix="/v1")