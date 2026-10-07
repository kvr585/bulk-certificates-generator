from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import jobs, certificates
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.db.database import init_db
from app.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: setup logging and initialize database tables
    setup_logging(debug=settings.DEBUG)
    logger.info("Initializing database tables...")
    init_db()
    logger.info("%s started successfully (Environment: %s)", settings.APP_NAME, settings.APP_ENV)
    yield
    # Shutdown
    logger.info("Application shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "Production-grade Bulk Certificate Generator API. "
        "Allows clients to submit batches of certificate recipients, processes them asynchronously, "
        "tracks progress and individual errors, and provides safe PDF retrieval."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware (permits local dashboards/clients)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Clean validation error formatting without stack traces."""
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append({
            "field": field,
            "message": err.get("msg"),
            "type": err.get("type"),
        })
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, errors)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content={"detail": "Request validation failed", "errors": errors},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch unhandled exceptions: log internal traceback on server,
    but never leak internal implementation or stack traces to API clients.
    """
    logger.error("Unhandled server error on %s %s: %s", request.method, request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please contact system support."},
    )


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Health check",
    description="Check server and database connectivity status.",
)
def health_check():
    return HealthResponse(
        status="healthy",
        version=settings.APP_VERSION,
        database="connected",
    )


# Root redirect or greeting
@app.get("/", tags=["System"], include_in_schema=False)
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "documentation": "/docs",
        "health": "/health",
        "api_v1": settings.API_V1_STR,
    }


# Include API v1 routes
app.include_router(jobs.router, prefix=settings.API_V1_STR)
app.include_router(certificates.router, prefix=settings.API_V1_STR)
