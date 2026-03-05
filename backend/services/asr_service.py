import os
from dotenv import load_dotenv
from faster_whisper import WhisperModel
from pathlib import Path
from loguru import logger
import torch
from pyannote.audio import Pipeline
import numpy as np

# ========== PyTorch 2.6 兼容性修复 ==========
# pyannote.audio 的模型文件需要 weights_only=False 才能正确加载
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load
# ============================================

class ASRService:
    def __init__(self, model_size="large-v3", device=None, compute_type="float16"):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.compute_type = compute_type if self.device == "cuda" else "int8"
        self.model_size = model_size
        self.model = None
        self.diarization_pipeline = None

    def load_model(self):
        if not self.model:
            logger.info(f"Loading Whisper model ({self.model_size}) on {self.device}...")
            try:
                from huggingface_hub import snapshot_download
                model_id = f"Systran/faster-whisper-{self.model_size}"
                logger.info(f"📥 Checking/Downloading model: {model_id} from HF Mirror...")
                
                cache_dir = os.path.join(os.getcwd(), "models", self.model_size)
                os.makedirs(cache_dir, exist_ok=True)
                
                model_path = snapshot_download(
                    repo_id=model_id, 
                    local_dir=cache_dir,
                    local_dir_use_symlinks=False,
                    resume_download=True
                )
                
                self.model = WhisperModel(
                    model_path, 
                    device=self.device, 
                    compute_type=self.compute_type
                )
                logger.info("✅ Whisper model loaded successfully.")
                
            except Exception as e:
                logger.error(f"❌ Failed to load Whisper model: {e}")
                raise e

    def load_diarization_pipeline(self):
        if not self.diarization_pipeline:
            logger.info("Loading Pyannote Diarization pipeline...")
            try:
                # Explicitly load .env file to ensure HF_TOKEN is available
                env_path = Path(__file__).resolve().parent.parent / ".env"
                if env_path.exists():
                    load_dotenv(env_path)
                else:
                    logger.warning(f".env file not found at {env_path}")

                # Note: This requires HF_TOKEN if using the official gated model.
                # If it fails, we might need to ask the user.
                # We use a fallback if possible, strictly for demo, but 3.1 is standard.
                auth_token = os.getenv("HF_TOKEN")
                
                if not auth_token:
                    logger.error("❌ HF_TOKEN not found in environment variables. Please check your .env file.")
                else:
                    auth_token = auth_token.strip()
                    logger.info(f"🔑 Using HF_TOKEN: {auth_token[:4]}...{auth_token[-4:]} (len={len(auth_token)})")

                # Fix: newer pyannote uses 'token' instead of deprecated 'use_auth_token'
                # Also ensure we are using the mirror
                os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"
                
                self.diarization_pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=auth_token
                )
                
                if self.diarization_pipeline is not None:
                     self.diarization_pipeline.to(torch.device(self.device))
                     logger.info("✅ Diarization pipeline loaded.")
                else:
                     logger.error("❌ Pipeline.from_pretrained returned None. Check HF permissions or token.")
            except Exception as e:
                logger.error(f"❌ Failed to load Diarization pipeline: {e}")
                import traceback
                logger.error(traceback.format_exc())
                logger.warning("⚠️ Diarization will be skipped. All text will be assigned to 'Speaker_0'.")
                self.diarization_pipeline = None

    def transcribe(self, audio_path: Path, language: str = None):
        """
        Transcribe audio file.
        Returns list of segments with timestamps and text.
        """
        # We now alias this to the method with diarization support, 
        # but for backward compatibility, we can just return the text segments if diarization fails.
        return self.transcribe_with_diarization(audio_path, language)

    def transcribe_with_diarization(self, audio_path: Path, language: str = None):
        self.load_model() 
        self.load_diarization_pipeline() # Try loading
        
        logger.info(f"Transcribing {audio_path}...")
        
        # 1. Transcribe
        segments, info = self.model.transcribe(
            str(audio_path), 
            language=language,
            beam_size=8,
            vad_filter=False
        )
        
        whisper_segments = []
        for segment in segments:
            whisper_segments.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
                "speaker": "SPEAKER_00" # Default
            })
            
        logger.info(f"Transcription complete. Found {len(whisper_segments)} segments.")

        # 2. Diarize (if available)
        if self.diarization_pipeline:
            try:
                logger.info("Running speaker diarization...")
                diarization = self.diarization_pipeline(str(audio_path))

                # Compatibility: pyannote may return Annotation directly,
                # or DiarizeOutput with .speaker_diarization Annotation.
                diarization_annotation = diarization
                if not hasattr(diarization_annotation, "itertracks"):
                    diarization_annotation = getattr(diarization, "speaker_diarization", None)
                if diarization_annotation is None or not hasattr(diarization_annotation, "itertracks"):
                    raise TypeError(f"Unsupported diarization output type: {type(diarization)}")
                
                # Merge speakers into whisper segments
                for segment in whisper_segments:
                    # Find dominant speaker in this segment range
                    start = segment["start"]
                    end = segment["end"]
                    
                    # Get all speakers overlapping with this segment
                    speakers = []
                    for turn, _, speaker in diarization_annotation.itertracks(yield_label=True):
                        # Calculate overlap
                        overlap_start = max(start, turn.start)
                        overlap_end = min(end, turn.end)
                        duration = max(0, overlap_end - overlap_start)
                        if duration > 0:
                            speakers.append((speaker, duration))
                    
                    if speakers:
                        # Sort by duration and pick the longest one
                        speakers.sort(key=lambda x: x[1], reverse=True)
                        segment["speaker"] = speakers[0][0]

                # Smooth unstable short segments to reduce speaker jitter/cross-talk
                for idx in range(1, len(whisper_segments) - 1):
                    cur = whisper_segments[idx]
                    prev_seg = whisper_segments[idx - 1]
                    next_seg = whisper_segments[idx + 1]
                    cur_dur = cur["end"] - cur["start"]

                    if (
                        cur_dur <= 1.6
                        and prev_seg.get("speaker") == next_seg.get("speaker")
                        and cur.get("speaker") != prev_seg.get("speaker")
                    ):
                        cur["speaker"] = prev_seg.get("speaker", cur.get("speaker"))
                        
                logger.info("✅ Diarization merged successfully.")
            except Exception as e:
                logger.error(f"Diarization failed: {e}")
                
        return whisper_segments

asr_service = ASRService()
