import socket
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response

from app.config import load_settings
from app.database import Database
from app.storage import ObjectStorage
from app import routes

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

HOSTNAME = socket.gethostname()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Starting application on host %s", HOSTNAME)
    
    settings = load_settings()
    
    database = Database(settings)
    object_storage = ObjectStorage(settings)
    
    routes.db = database
    routes.storage = object_storage
    
    logger.info("Application startup complete")
    yield
    
    database.close()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Document Archiving System",
    description="A secure, multi-tier document archiving API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def add_served_by_header(request: Request, call_next):
    """Add X-Served-By header to every response for load balancing verification."""
    response = await call_next(request)
    response.headers["X-Served-By"] = HOSTNAME
    return response


@app.get("/health")
async def health_check():
    """Health check endpoint used by Docker and NGINX."""
    return {"status": "healthy", "host": HOSTNAME}


app.include_router(routes.router)
