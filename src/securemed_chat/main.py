"""
Main Application Entry Point.

This file configures and starts the FastAPI application. It creates the main
FastAPI instance and includes the API router that defines all the
application's endpoints.

To run the application:
    uvicorn src.securemed_chat.main:app --reload
"""
from fastapi import FastAPI
from src.securemed_chat.api.endpoints import router as api_router

# Create the FastAPI application instance
app = FastAPI(
    title="SecureMed Chat API",
    description="An API to help patients prepare for their doctor's visit.",
    version="1.0.0"
)

# Include the API router
# All routes defined in api/endpoints.py will be available under the main app.
app.include_router(api_router, prefix="/api", tags=["Medical Chat"])

@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the SecureMed Chat API. Go to /docs for the API documentation."}
