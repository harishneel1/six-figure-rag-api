from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.userRoutes import router as userRoutes

# Create FastAPI app
app = FastAPI(
    title="Six-Figure AI Engineering API",
    description="Backend API for Six-Figure AI Engineering application",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(userRoutes, prefix="/api/user")

"""
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}
"""
