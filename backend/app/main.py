"""FastAPI Main Application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.api.router import api_router
from app.core.db import SessionLocal
from app.services.evaluation import evaluate_targets_for_date

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    docs_url=f"{settings.API_V1_PREFIX}/docs",
    redoc_url=f"{settings.API_V1_PREFIX}/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Create scheduler
scheduler = BackgroundScheduler()


def daily_evaluation_task():
    """
    Daily task to evaluate all active targets.
    Runs at 23:59 UTC daily.
    """
    print(f"[{datetime.now(timezone.utc)}] Running daily target evaluation...")
    
    db = SessionLocal()
    try:
        # Evaluate today's targets
        today = datetime.now(timezone.utc).date()
        evaluations = evaluate_targets_for_date(today, db)
        print(f"Created {len(evaluations)} evaluations for {today}")
    except Exception as e:
        print(f"Error in daily evaluation: {e}")
        db.rollback()
    finally:
        db.close()


@app.get("/")
def root():
    """Root endpoint - API information"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": f"{settings.API_V1_PREFIX}/docs",
    }


@app.on_event("startup")
async def startup_event():
    """Execute on application startup"""
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Debug mode: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE_URL}")
    
    # Start scheduler
    scheduler.add_job(
        daily_evaluation_task,
        trigger=CronTrigger(hour=23, minute=59),  # Run at 23:59 UTC daily
        id="daily_evaluation",
        name="Daily Target Evaluation",
        replace_existing=True
    )
    scheduler.start()
    print("Scheduler started: Daily evaluation at 23:59 UTC")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown"""
    print(f"Shutting down {settings.APP_NAME}")
    
    # Shutdown scheduler
    if scheduler.running:
        scheduler.shutdown()
        print("Scheduler stopped")
