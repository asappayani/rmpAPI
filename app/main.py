from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import professor_router, school_router

# Create FastAPI app instance
app = FastAPI(
    title="RMP API",
    description="A FastAPI wrapper around Rate My Professors data",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware (optional, but useful for web frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(professor_router.router, prefix="/api/v1")
app.include_router(school_router.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to RMP API",
        "docs": "/docs",
        "redoc": "/redoc",
        "version": "0.1.0"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}