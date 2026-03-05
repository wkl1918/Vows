import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Set HuggingFace Mirror for China (Speed up model downloads)
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import HfApi, login

# Load env variables
env_path = Path(r"D:\vid\VoxFlow\backend\.env")
load_dotenv(env_path)
token = os.getenv("HF_TOKEN")

print(f"Token loaded: {token[:4]}...{token[-4:] if token else 'None'}")

if not token:
    print("FATAL: No token found")
    sys.exit(1)

# Try login (stores git credential, but we just want to test api)
try:
    login(token=token)
    print("Login successful.")
except Exception as e:
    print(f"Login failed: {e}")

api = HfApi(token=token)

models_to_check = [
    "pyannote/speaker-diarization-3.1",
    "pyannote/segmentation-3.0"
]

print("\nChecking permissions...")
for model_id in models_to_check:
    try:
        info = api.model_info(model_id)
        print(f"✅ Access granted to {model_id}")
    except Exception as e:
        print(f"❌ Access denied to {model_id}: {e}")
