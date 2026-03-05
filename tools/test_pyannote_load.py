"""
Test loading pyannote model.
Usage (PowerShell):
  $env:HF_TOKEN='hf_xxx'
  python tools/test_pyannote_load.py
"""
import os

hf_token = os.getenv("HF_TOKEN", "").strip()
if not hf_token:
    raise RuntimeError("HF_TOKEN is required. Set it in environment before running.")

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

print("Step 1: Validate token...")
from huggingface_hub import HfApi
api = HfApi(token=hf_token)
user_info = api.whoami()
print(f"Token valid. User: {user_info.get('name', 'unknown')}")

print("\nStep 2: Load pyannote model...")
try:
    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=hf_token,
    )
    print("SUCCESS: Pipeline loaded.")
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
