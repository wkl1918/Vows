import os
import sys
from pathlib import Path

# Fix Windows console encoding (avoid GBK encode errors for emoji/unicode)
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Set HuggingFace Mirror for China (Speed up model downloads)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# === FFmpeg Shared Libraries (Required by torchcodec / torchaudio / demucs) ===
# Must be loaded BEFORE importing torch/torchaudio
# __file__ = D:\vid\VoxFlow\backend\app.py -> parent.parent = D:\vid\VoxFlow
FFMPEG_SHARED_DIR = Path(__file__).resolve().parent.parent / "tools" / "ffmpeg"
if FFMPEG_SHARED_DIR.exists() and os.name == 'nt':
    os.add_dll_directory(str(FFMPEG_SHARED_DIR))
    os.environ["PATH"] = str(FFMPEG_SHARED_DIR) + os.pathsep + os.environ["PATH"]
    print(f"✅ Added FFmpeg shared DLLs: {FFMPEG_SHARED_DIR}")
else:
    print(f"⚠️  FFmpeg shared dir not found at: {FFMPEG_SHARED_DIR}")

# Fix for Windows DLL load failure
# PyTorch 2.10+cu128 bundles CUDA runtime, but we still add torch/lib to PATH
if os.name == 'nt':
    try:
        import torch
        torch_lib_path = Path(os.path.dirname(torch.__file__)) / "lib"
        if torch_lib_path.exists():
            os.add_dll_directory(str(torch_lib_path))
            os.environ["PATH"] = str(torch_lib_path) + os.pathsep + os.environ["PATH"]
            print(f"✅ Added Torch DLL path: {torch_lib_path}")

        print(f"✅ PyTorch {torch.__version__}, CUDA available: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"✅ GPU: {torch.cuda.get_device_name(0)}")
    except ImportError:
        print("⚠️  PyTorch not found. GPU inference will not be available.")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from core.config import settings
from api import tasks

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# CORS Configuration (Allow Frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])

@app.get("/")
def read_root():
    return {"message": "VoxFlow Backend is Running!", "docs": "/docs"}

if __name__ == "__main__":
    print("Starting VoxFlow Backend...")
    # Using "app:app" string for reload support
    # Removed reload=True for better stability and clean shutdown on Windows
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
