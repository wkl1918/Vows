import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory is the backend folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

# Storage configuration
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"
TEMP_DIR = STORAGE_DIR / "temp"

# Create directories if they don't exist
for d in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class Settings:
    PROJECT_NAME: str = "VoxFlow API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
settings = Settings()
