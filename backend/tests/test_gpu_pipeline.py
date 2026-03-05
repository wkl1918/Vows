import torch
import torchaudio
import numpy as np
import os
import demucs.separate
from demucs.apply import apply_model
from demucs.pretrained import get_model
import soundfile as sf

TEST_FILE = "test_tone.wav"
OUTPUT_DIR = "separated_test"

def create_dummy_audio():
    print(f"🎵 Creating dummy audio file: {TEST_FILE}")
    sr = 44100
    duration = 5
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    # 440Hz sine wave (Left) and 880Hz (Right)
    sig_l = 0.5 * np.sin(2 * np.pi * 440 * t)
    sig_r = 0.5 * np.sin(2 * np.pi * 880 * t)
    audio = np.stack([sig_l, sig_r], axis=1) # (N, 2)
    sf.write(TEST_FILE, audio, sr)
    return TEST_FILE

def test_demucs_gpu():
    print(f"🚀 Starting Demucs Inference Test on {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}...")
    
    # 1. Load Model
    print("📦 Loading Demucs model (htdemucs)...")
    model = get_model('htdemucs')
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    
    # 2. Load Audio
    print("🎧 Loading Audio...")
    wav, sr = torchaudio.load(TEST_FILE)
    wav = wav.to(device)
    # Demucs expects (Channels, Time)
    # torchaudio loads (Channels, Time) - perfect.
    
    # Add batch dimension: (1, Channels, Time)
    wav = wav.unsqueeze(0) 

    # 3. Separate
    print("✨ Separating... (This verifies CUDA memory allocation)")
    # apply_model(model, mix, shifts=1, split=True, overlap=0.25, transition_power=1., progress=True, device=None, num_workers=0, segment=None, **kwargs)
    ref = wav.mean(0)
    wav = (wav - ref.mean()) / ref.std()
    
    sources = apply_model(model, wav, shifts=0, split=True, progress=False, device=device)
    
    # sources shape: (Batch, Sources, Channels, Time)
    print(f"✅ Separation Complete! Output Shape: {sources.shape}")
    print("   (Expect keys: drums, bass, other, vocals)")
    
    # Cleanup
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
    print("🧹 Cleaned up test file.")

if __name__ == "__main__":
    try:
        create_dummy_audio()
        test_demucs_gpu()
        print("\n🎉 SUCCESS: GPU Inference works correctly!")
    except Exception as e:
        print(f"\n❌ ERROR: GPU Test Failed - {e}")
        import traceback
        traceback.print_exc()
