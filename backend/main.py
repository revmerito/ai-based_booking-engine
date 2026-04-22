"""
Main Application Entry Point
FastAPI app initialization with all routers.
Production-ready with CORS, lifespan events.
"""
from contextlib import asynccontextmanager
import logging
import sys
import asyncio

# Windows specific: Fix asyncio loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Reload Trigger 2026-04-22 - Force Fresh Build
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from app.core.config import get_settings
from app.core.database import init_db

# Import routers
from app.api.v1 import auth, users, hotels, rooms, bookings, dashboard, rates, payments, availability, reports, public, integration, upload, addons, channel_manager, amenities, properties, competitors, admin

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup aur shutdown events handle karta hai.
    Database tables create hote hain startup par.
    """
    # Startup: Database initialize karo
    logger.info("Starting Hotelier Hub API...")
    await init_db()
    logger.info("Database initialized successfully!")
    yield
    # Shutdown: Cleanup if needed
    logger.info("Shutting down...")


# FastAPI app create karo
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-tenant Hotel Management API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error caught: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )

# CORS Middleware - Frontend ko allow karna hai
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Server health check"""
    return {"status": "healthy", "version": settings.APP_VERSION}


# API Version 1 routers include karo
API_V1_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=API_V1_PREFIX)
app.include_router(users.router, prefix=API_V1_PREFIX)
app.include_router(hotels.router, prefix=API_V1_PREFIX)
app.include_router(rooms.router, prefix=API_V1_PREFIX)
app.include_router(bookings.router, prefix=API_V1_PREFIX)
app.include_router(dashboard.router, prefix=API_V1_PREFIX)
app.include_router(rates.router, prefix=API_V1_PREFIX)
app.include_router(payments.router, prefix=API_V1_PREFIX)
app.include_router(availability.router, prefix=API_V1_PREFIX)
app.include_router(reports.router, prefix=API_V1_PREFIX)
app.include_router(public.router, prefix=API_V1_PREFIX)
app.include_router(integration.router, prefix=API_V1_PREFIX)
app.include_router(upload.router, prefix=API_V1_PREFIX)
app.include_router(addons.router, prefix=API_V1_PREFIX)
app.include_router(channel_manager.router, prefix=API_V1_PREFIX)
app.include_router(amenities.router, prefix=API_V1_PREFIX)
app.include_router(properties.router, prefix=API_V1_PREFIX)
app.include_router(competitors.router, prefix=API_V1_PREFIX)
app.include_router(admin.router, prefix=API_V1_PREFIX)

# Mount Static Files
import os
from pathlib import Path
from fastapi.staticfiles import StaticFiles
BACKEND_DIR = Path(__file__).resolve().parent
STATIC_DIR = BACKEND_DIR / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """API root - basic info"""
    return {
        "message": "Welcome to Hotelier Hub API",
        "docs": "/docs",
        "version": settings.APP_VERSION
    }
