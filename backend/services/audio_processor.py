import os
import subprocess
import torch
import demucs.separate
from pathlib import Path
from loguru import logger
import imageio_ffmpeg
from pydub import AudioSegment

class AudioProcessor:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Dynamically get FFmpeg path
        self.ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        logger.info(f"Using FFmpeg binary at: {self.ffmpeg_exe}")
        
        # Configure pydub to use our ffmpeg binary
        AudioSegment.converter = self.ffmpeg_exe
        
        # Add FFmpeg to system PATH for other tools (Demucs, etc.)
        ffmpeg_dir = os.path.dirname(self.ffmpeg_exe)
        if ffmpeg_dir not in os.environ["PATH"]:
             os.environ["PATH"] += os.pathsep + ffmpeg_dir
             logger.info(f"Added FFmpeg dir to PATH: {ffmpeg_dir}")

        # Add FFmpeg SHARED libraries to PATH (needed by torchcodec in subprocesses like Demucs)
        ffmpeg_shared_dir = Path(__file__).resolve().parent.parent.parent / "tools" / "ffmpeg"
        if ffmpeg_shared_dir.exists():
            ffmpeg_shared_str = str(ffmpeg_shared_dir)
            if ffmpeg_shared_str not in os.environ["PATH"]:
                os.environ["PATH"] = ffmpeg_shared_str + os.pathsep + os.environ["PATH"]
                logger.info(f"Added FFmpeg shared DLLs to PATH: {ffmpeg_shared_str}")
            # Also register DLL directory for current process
            try:
                os.add_dll_directory(ffmpeg_shared_str)
            except OSError:
                pass

        # Add Python Scripts dir to PATH (where 'demucs', 'edge-tts' live)
        import sys
        scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
        if os.path.exists(scripts_dir) and scripts_dir not in os.environ["PATH"]:
             os.environ["PATH"] += os.pathsep + scripts_dir
             logger.info(f"Added Scripts dir to PATH: {scripts_dir}")

    def extract_audio(self, video_path: Path, output_path: Path) -> Path:
        """
        Extract audio from video using FFmpeg.
        Returns the path to the extracted audio file.
        """
        logger.info(f"Extracting audio from {video_path} to {output_path}")
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists():
            os.remove(output_path)

        command = [
            self.ffmpeg_exe, # Use absolute path
            "-i", str(video_path),
            "-vn",              # No video
            "-acodec", "pcm_s16le", # WAV format
            "-ar", "44100",     # 44.1kHz
            "-ac", "2",         # Stereo
            str(output_path),
            "-y"                # Overwrite
        ]
        
        try:
            # Use shell=False for security, but allow window creation on Windows if needed
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not output_path.exists():
                raise FileNotFoundError(f"FFmpeg failed to create {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg Error: {e.stderr.decode()}")
            raise RuntimeError(f"FFmpeg failed: {e.stderr.decode()}")

    def separate_vocals(self, audio_path: Path, output_dir: Path):
        """
        Separate audio into vocals and background music using Demucs.
        Returns paths to (vocals, accompaniment).
        """
        logger.info(f"Separating vocals for {audio_path} on {self.device}...")
        
        # Demucs command wrapper
        # We use the CLI interface for simplicity as it handles loading/saving/memory well
        command = [
            "demucs",
            "--two-stems=vocals", # Only separate vocals/accompaniment
            "-n", "htdemucs",     # Model
            "-d", self.device,
            "--out", str(output_dir),
            str(audio_path)
        ]

        try:
            # Removed PIPE to allow output to show in the terminal (User can see progress bar)
            logger.info(f"Running Demucs command: {' '.join(command)}")
            subprocess.run(command, check=True)
            
            # Construct expected paths
            # Demucs structure: <out_dir>/htdemucs/<track_name>/vocals.wav
            track_name = audio_path.stem
            model_out_dir = output_dir / "htdemucs" / track_name
            
            vocals_path = model_out_dir / "vocals.wav"
            no_vocals_path = model_out_dir / "no_vocals.wav"
            
            if not vocals_path.exists() or not no_vocals_path.exists():
                raise FileNotFoundError("Demucs output files not found.")
            
            # CLEAR GPU MEMORY after Demucs
            if self.device == "cuda":
                logger.info("🧹 Clearing GPU memory after extraction...")
                import torch
                torch.cuda.empty_cache()
                import gc
                gc.collect()

            return vocals_path, no_vocals_path

        except subprocess.CalledProcessError as e:
            logger.error(f"Demucs Error: {e}")
            raise RuntimeError("Demucs separation failed.")

    def cut_audio_segment(self, input_path: Path, start_sec: float, end_sec: float, output_path: Path):
        """
        Cut a segment of audio from start to end (seconds).
        """
        try:
            audio = AudioSegment.from_file(input_path)
            # pydub works in milliseconds
            start_ms = int(start_sec * 1000)
            end_ms = int(end_sec * 1000)
            
            chunk = audio[start_ms:end_ms]
            chunk.export(output_path, format="wav")
            return output_path
        except Exception as e:
            logger.error(f"Failed to cut audio: {e}")
            raise

    def merge_video_audio(self, video_path: Path, dub_audio_path: Path, bgm_audio_path: Path, output_path: Path):
        """
        Mixes Dubbing + BGM and merges with original Video.
        """
        logger.info(f"Merging final video to {output_path}...")
        
        # Adjust volumes:
        # - Dub: 1.0
        # - BGM(no_vocals): 0.30
        # - Original track: 0.04
        # Inputs: 0: Video(original), 1: Dub, 2: BGM(no_vocals)
        
        # We need to ensure 'dub' and 'bgm' are same length or handle shortest.
        # amix=duration=first (assume Video/BGM length). 
        # Actually 'longest' is safer to not cut off tails, but we want video length.
        
        command = [
            self.ffmpeg_exe, # Use absolute path
            "-i", str(video_path),
            "-i", str(dub_audio_path),
            "-i", str(bgm_audio_path),
            "-filter_complex", "[1:a]volume=1.0[dub];[2:a]volume=0.30[bgm];[0:a]volume=0.04[orig];[dub][bgm][orig]amix=inputs=3:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",     # Use original video
            "-map", "[aout]",  # Use mixed audio
            "-c:v", "copy",    # Reuse video stream (fast)
            "-c:a", "aac",
            "-b:a", "192k",
            str(output_path),
            "-y"
        ]

        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if not output_path.exists():
                raise FileNotFoundError("Merged video file not created.")
            return output_path
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg Merge Error: {e.stderr.decode()}")
            raise RuntimeError(f"FFmpeg Merge failed: {e.stderr.decode()}")

audio_processor = AudioProcessor()
