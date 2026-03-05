import torch
import sys
import os

def check_environment():
    print("="*50)
    print("VoxFlow Environment Check")
    print("="*50)
    
    # 1. Check CUDA
    print(f"Python Version: {sys.version}")
    try:
        import torch
        print(f"PyTorch Version: {torch.__version__}")
        if torch.cuda.is_available():
            print(f"✅ CUDA is available: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA Version: {torch.version.cuda}")
        else:
            print("⚠️  CUDA is NOT available. Running on CPU (will be slow).")
    except ImportError:
        print("❌ PyTorch not found!")
        
    # 2. Check Demucs Import
    try:
        import demucs
        from demucs.pretrained import get_model
        print(f"✅ Demucs library found (Version: {demucs.__version__})")
        
        # Optional: Try to load model config (might trigger download, so we just check import for now)
        # model = get_model('htdemucs')
        # print("✅ Demucs model registry accessible")
    except ImportError as e:
        print(f"❌ Failed to import Demucs: {e}")
    except Exception as e:
        print(f"⚠️  Demucs check warning: {e}")

    # 3. Check Faster-Whisper
    try:
        import faster_whisper
        print(f"✅ Faster-Whisper found (Version: {faster_whisper.__version__})")
    except ImportError:
        print("❌ Faster-Whisper not found!")

    # 4. Check FFmpeg (via ffmpeg-python)
    try:
        import ffmpeg
        print("✅ ffmpeg-python library found")
        # We assume the binary is in path or handled by OS
    except ImportError:
        print("❌ ffmpeg-python not found!")

    print("="*50)

if __name__ == "__main__":
    check_environment()
