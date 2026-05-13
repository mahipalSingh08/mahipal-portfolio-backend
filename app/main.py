from app.routes import reaction
from contextlib import asynccontextmanager

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_mongo_connection, connect_to_mongo
from app.routes import health, contact, auth

settings = get_settings()
settings.validate()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await connect_to_mongo()
    try:
        yield
    finally:
        await close_mongo_connection()


app = FastAPI(
    title=settings.app_name,
    description="Backend API for Angular Portfolio Application",
    version=settings.app_version,
    docs_url="/docs" if settings.enable_docs else None,
    redoc_url="/redoc" if settings.enable_docs else None,
    openapi_url="/openapi.json" if settings.enable_docs else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(auth.router, prefix="/api", tags=["Auth"])
app.include_router(reaction.router, prefix="/api", tags=["Reaction"])
app.include_router(contact.router, prefix="/api", tags=["Contact"])


@app.get("/")
async def root():
    response = {"message": "Welcome to the Portfolio Backend API."}
    if settings.enable_docs:
        response["docs"] = "/docs"

    return response
