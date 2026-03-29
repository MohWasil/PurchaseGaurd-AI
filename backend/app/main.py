# """
# Main FastAPI Application
# """
# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from contextlib import asynccontextmanager
# import os

# from app.core.database import init_db
# from app.api import auth
# from app.api import purchases  # Add this import

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Application lifespan - initialize DB on startup"""
#     # Ensure data directories exist
#     os.makedirs("data/receipts", exist_ok=True)
#     os.makedirs("data/encrypted", exist_ok=True)
    
#     await init_db()
#     yield

# app = FastAPI(
#     title="PurchaseGuard AI",
#     description="Personal Receipt & Warranty Intelligence Agent",
#     version="1.0.0",
#     lifespan=lifespan
# )

# # CORS Middleware (allow Streamlit frontend)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(auth.router, prefix="/api/v1")
# app.include_router(purchases.router, prefix="/api/v1")  # Add this line

# @app.get("/")
# async def root():
#     """Health check endpoint"""
#     return {"status": "healthy", "service": "PurchaseGuard AI"}

# @app.get("/api/v1/health")
# async def health_check():
#     """API health check"""
#     return {"status": "ok", "version": "1.0.0"}


"""
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.core.database import init_db
from app.core.scheduler import scheduler
from app.api import auth
from app.api import purchases

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize DB and scheduler on startup"""
    # Ensure data directories exist
    os.makedirs("data/receipts", exist_ok=True)
    os.makedirs("data/encrypted", exist_ok=True)
    
    # Initialize database
    await init_db()
    
    # Start background scheduler
    scheduler.start()
    
    yield
    
    # Shutdown scheduler on app close
    scheduler.shutdown()

# app = FastAPI(
#     title="PurchaseGuard AI",
#     description="Personal Receipt and Warranty Intelligence Agent",
#     version="1.0.0",
#     lifespan=lifespan
# )

app = FastAPI(
    title="PurchaseGuard AI",
    description="Personal Receipt & Warranty Intelligence Agent",
    version="1.0.0",
    lifespan=lifespan
    # openapi_url="/openapi.json",  # Force refresh
    # docs_url="/docs"
)

# CORS Middleware (allow Streamlit frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=True,
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(purchases.router, prefix="/api/v1")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PurchaseGuard AI"}

@app.get("/api/v1/health")
async def health_check():
    """API health check"""
    return {"status": "ok", "version": "1.0.0"}

import logging
@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    logging.Logger.error(f"422 Error: {str(exc)}")
    logging.Logger.error(f"Request: {request.url}")
    logging.Logger.error(f"Details: {exc.errors()}")
    return {"detail": "Validation Error", "errors": exc.errors()}