from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.userRoutes import router as userRoutes
from src.routes.projectRoutes import router as projectRoutes
from src.routes.projectFilesRoutes import router as projectFilesRoutes
from src.routes.chatRoutes import router as chatRoutes
from src.config.logging import configure_logging, get_logger
from src.middleware.logging_middleware import LoggingMiddleware

# Configure logging before anything else
configure_logging()
logger = get_logger(__name__)

logger.info("initializing_application", version="1.0.0")

# Create FastAPI app
app = FastAPI(
    title="Six-Figure AI Engineering API",
    description="Backend API for Six-Figure AI Engineering application",
    version="1.0.0",
)

# Add logging middleware (should be first to capture all requests)
app.add_middleware(LoggingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("middleware_configured")

app.include_router(userRoutes, prefix="/api/user")
app.include_router(projectRoutes, prefix="/api/projects")
app.include_router(projectFilesRoutes, prefix="/api/projects")
app.include_router(chatRoutes, prefix="/api/chats")

logger.info("routes_registered", route_count=4)

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    logger.debug("health_check_called")
    return {"status": "healthy", "version": "1.0.0"}

logger.info("application_ready")
