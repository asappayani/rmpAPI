from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.routers import professor_router, school_router

# Create FastAPI app instance
app = FastAPI(
    title="RMP API",
    description="A FastAPI wrapper around Rate My Professors data",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # remember to add my frontend url here
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
    
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