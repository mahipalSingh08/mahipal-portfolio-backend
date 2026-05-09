# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.database import connect_to_mongo, close_mongo_connection
from app.routes import health, contact

# Initialize FastAPI application
app = FastAPI(
    title="Portfolio Backend API",
    description="Backend API for Angular Portfolio Application",
    version="1.0.0"
)

# Configure CORS for the Angular frontend
# You can restrict this to your specific frontend URL in production
origins = [
    "http://localhost:4200", # Default Angular local development server
    "http://127.0.0.1:4200",
    "https://www.mahipal.tech", # Production frontend URL
    "https://mahipal.tech" # Production frontend URL without www
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Application startup and shutdown events to handle MongoDB connection
@app.on_event("startup")
async def startup_db_client():
    await connect_to_mongo()

@app.on_event("shutdown")
async def shutdown_db_client():
    await close_mongo_connection()

# Include Routers
app.include_router(health.router, tags=["Health"])
app.include_router(contact.router, prefix="/api", tags=["Contact"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Portfolio Backend API. Visit /docs for Swagger UI."}
