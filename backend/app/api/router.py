"""API Router - Aggregates all API routes"""
from fastapi import APIRouter
from .endpoints import health, auth, users, categories, sessions, stats, heatmap, targets, evaluations, notifications, admin

# Create main API router
api_router = APIRouter()

# Include health check endpoint
api_router.include_router(health.router, tags=["health"])

# Include authentication endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Include user endpoints
api_router.include_router(users.router, prefix="/users", tags=["users"])

# Include category endpoints
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])

# Include session endpoints
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])

# Include stats endpoints
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])

# Include heatmap endpoints
api_router.include_router(heatmap.router, prefix="/heatmap", tags=["heatmap"])

# Include work targets endpoints
api_router.include_router(targets.router, prefix="/targets", tags=["targets"])

# Include evaluations endpoints
api_router.include_router(evaluations.router, prefix="/evaluations", tags=["evaluations"])

# Include notifications endpoints
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Include admin endpoints
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

# TODO: Add more routers as you develop your application
# Example:
# from .endpoints import items
# api_router.include_router(items.router, prefix="/items", tags=["items"])
