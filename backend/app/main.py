from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.routes import auth, recommend, chat, admin
import app.models

# Create tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered health insurance recommendation platform API",
    version="1.0.0"
)

# CORS configuration for local React development
origins = [
    "http://localhost:5173", # Vite Default Port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Prefix route inclusion block
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(recommend.router, prefix="/api/recommend", tags=["Recommendations"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat Support"])
app.include_router(admin.router, prefix="/api/admin", tags=["Administration"])

# Universal Health Check Route
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "aarogyaaid-backend"
    }