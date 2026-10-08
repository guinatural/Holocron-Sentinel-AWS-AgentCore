"""FastAPI application for Holocron Sentinel API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router

# Create FastAPI app
app = FastAPI(
    title="Holocron Sentinel V2 API",
    description="Multi-tenant security auditing API with LGPD compliance",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(api_router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Holocron Sentinel V2",
        "version": "2.0.0",
        "description": "Multi-tenant security auditing API with LGPD compliance",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/status")
async def status():
    """API status endpoint."""
    return {
        "status": "running",
        "service": "Holocron Sentinel V2",
        "version": "2.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
