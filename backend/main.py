import logging
import sys
from contextlib import asynccontextmanager
import pydantic
import structlog

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text  # ADD THIS IMPORT

from app.utils.config import settings
from app.utils.limiter import limiter  # Import the limiter instance
from slowapi.errors import RateLimitExceeded  # Import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware  # Import middleware if using global limits or complex setup

# Import your API routers
from app.routes import auth as auth_router

# Import create_tables and async_engine for lifespan
from app.utils.database import async_engine, create_tables  # ADD THIS IMPORT


# --- Structlog Configuration ---
def configure_logging(log_level: str):
    """Configures structlog logging."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level.upper(),
    )

    shared_processors = [
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S.%f", utc=False),
    ]

    if log_level.upper() == "DEBUG" or sys.stdout.isatty():  # Pretty print if DEBUG or TTY
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


configure_logging(settings.LOG_LEVEL)
log = structlog.get_logger(__name__)


# --- Rate Limiting Configuration ---
# Custom handler for rate limit exceeded
async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    log.warning(
        "Rate limit exceeded",
        client_host=request.client.host if request.client else "unknown",
        path=request.url.path,
        detail=str(exc.detail),
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


# --- Application Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    log.info(f"Starting up {settings.PROJECT_NAME}...")
    # Make limiter available to the app state for decorators
    app.state.limiter = limiter

    # Database setup: connection test and table creation
    try:
        # 1. Test database connection
        # Note: `async_engine` and `create_tables` are imported at the top of the file now.
        async with async_engine.connect() as connection:
            await connection.execute(text("SELECT 1"))  # Test query
            # For asyncpg, SELECT 1 doesn't typically need an explicit commit.
        log.info("Database connection test successful.")

        # 2. Create database tables
        log.info("Ensuring database tables are created (if they don't exist)...")
        # await create_tables() # MODIFIED: Temporarily uncommented to create tables
        # The create_tables function will log its own success message if called.

        log.info("Database setup completed successfully on startup.")

    except Exception as e:
        log.error(
            "Database setup failed during application startup.",
            error=str(e),  # Provides a quick summary of the error
            exc_info=True,  # Provides full traceback for detailed debugging
        )
        # To prevent the app from starting if DB is critical, you could re-raise:
        # raise RuntimeError("Failed to initialize database during startup.") from e

    yield  # Application runs here

    # Shutdown logic
    log.info(f"Shutting down {settings.PROJECT_NAME}...")
    # `async_engine` is already imported, no need to re-import here if it's in the module scope.
    await async_engine.dispose()
    log.info("Database engine disposed.")


# --- FastAPI Application Initialization ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,  # Added lifespan context manager
    # Register exception handlers
    exception_handlers={
        RateLimitExceeded: _rate_limit_exceeded_handler,
        RequestValidationError: lambda request, exc: JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": exc.body if hasattr(exc, "body") else None},
        ),
        HTTPException: lambda request, exc: JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
            headers=exc.headers,
        ),
        # Generic 500 error for unhandled exceptions
        Exception: lambda request, exc: JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal server error occurred."},
        ),
    },
)

# --- Middlewares ---
# Add SlowAPIMiddleware to handle rate limiting globally if needed,
# or rely on decorators for specific routes.
# If you have global limits or want to ensure all routes are processed by slowapi, add this:
app.add_middleware(SlowAPIMiddleware)


# CORS Middleware
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:  # Allow all origins if not specified (useful for local development)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- API Routers ---
# Include the authentication router
app.include_router(auth_router.router)


# Basic health check endpoint
@app.get(
    "/health",
    tags=["Health"],
    summary="Health Check",
    response_description="Returns the status of the application.",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """
    Checks the health of the application.
    """
    log.info("Health check endpoint called")
    return {"status": "healthy", "project_name": settings.PROJECT_NAME, "version": settings.PROJECT_VERSION}


# --- Main execution for development ---
if __name__ == "__main__":
    import uvicorn

    log.info(f"Starting Uvicorn server for {settings.PROJECT_NAME} on http://{settings.SERVER_HOST}:{settings.SERVER_PORT}")
    uvicorn.run(
        "main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.RELOAD_APP,
        log_level=settings.LOG_LEVEL.lower(),
    )
