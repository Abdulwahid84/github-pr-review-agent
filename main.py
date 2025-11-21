from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import review_routes
from app.utils.logger import setup_logger
import uvicorn

# Setup logger
logger = setup_logger()

# Initialize FastAPI app
app = FastAPI(
    title="GitHub PR Review Agent",
    description="Automated GitHub Pull Request Review using Multi-Agent AI System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(review_routes.router, prefix="/api", tags=["review"])

@app.get("/")
async def root():
    return {
        "message": "GitHub PR Review Agent API",
        "status": "running",
        "endpoints": {
            "review": "/api/review"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting GitHub PR Review Agent...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)