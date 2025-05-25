import logging
import sys
import pydantic
import structlog

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from app.utils.config import settings
from app.utils.rate_limiting import limiter, custom_rate_limit_handler
from app.routes import auth

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

    if log_level.upper() == "DEBUG" or sys.stdout.isatty(): # Pretty print if DEBUG or TTY
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

# --- FastAPI Application Initialization ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="0.1.0" # You can make this dynamic if needed
)

# --- Rate Limiting Setup ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

# --- CORS Middleware ---
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip() for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    log.info("CORS middleware enabled", origins=settings.CORS_ORIGINS)

# --- Exception Handlers ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    log.error("Request validation error", errors=exc.errors(), body=exc.body, url=str(request.url))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )

@app.exception_handler(pydantic.ValidationError)
async def pydantic_validation_exception_handler(request: Request, exc: pydantic.ValidationError):
    log.error("Pydantic validation error", errors=exc.errors(), url=str(request.url))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Pydantic Validation Error", "errors": exc.errors()},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    log.error(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url)
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    log.exception("Unhandled exception occurred", url=str(request.url)) # .exception logs with exc_info
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

# --- API Endpoints ---
@app.get(
    f"{settings.API_V1_STR}/health",
    tags=["Health"],
    summary="Health Check",
    response_description="Returns the health status of the API.",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """
    Endpoint to check the health of the application.
    """
    log.info("Health check endpoint called")
    return {"status": "healthy", "project_name": settings.PROJECT_NAME}

# --- Include Routers ---
app.include_router(auth.router)

# --- Application Lifecycle Events (Optional) ---
@app.on_event("startup")
async def startup_event():
    log.info(f"Starting up {settings.PROJECT_NAME}...")
    # Check database connection on startup
    try:
        from app.utils.database import async_engine
        async with async_engine.connect() as connection:
            log.info("Database connection successful on startup.")
    except Exception as e:
        log.error("Database connection failed on startup.", error=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    log.info(f"Shutting down {settings.PROJECT_NAME}...")
    # Cleanup database connections
    from app.utils.database import async_engine
    await async_engine.dispose()
    log.info("Database engine disposed.")

if __name__ == "__main__":
    import uvicorn
    log.info(f"Starting Uvicorn server for {settings.PROJECT_NAME} on http://localhost:8000")
    # Note: Uvicorn's access logs might not be structlog formatted by default here.
    # For full structlog integration with Uvicorn access logs, you'd typically run uvicorn
    # programmatically with a custom log_config or use a Gunicorn worker with Uvicorn.
    uvicorn.run(app, host="0.0.0.0", port=8000)
