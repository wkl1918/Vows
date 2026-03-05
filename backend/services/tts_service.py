import edge_tts
import asyncio
import os
import torch
import json
from pathlib import Path
from loguru import logger
from typing import List, Optional, Dict
from pydub import AudioSegment
import importlib
import sys
from concurrent.futures import ThreadPoolExecutor

# Try to import index-tts logic, but do it safely
# Note: We use IndexTTS via CLI subprocess, so we only need to verify it's installed
try:
    import indextts
    HAS_INDEXTTS = True
    logger.info(f"IndexTTS found at: {indextts.__file__}")
except ImportError:
    HAS_INDEXTTS = False
    logger.warning("IndexTTS not found. Voice cloning via IndexTTS will be unavailable.")

class TTSService:
    def __init__(self):
        self.reference_cache = {} # Cache speaker reference audio paths
        indextts_dir_env = os.getenv("INDEXTTS_DIR", "").strip()
        self.indextts_dir = Path(indextts_dir_env) if indextts_dir_env else None
        self._tts_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="edge-tts")

    async def generate_cloned_audio_batch(self, jobs: List[dict], output_dir: Path) -> Dict[int, str]:
        """
        Batch clone with one IndexTTS process/model load.
        Returns map: segment_index -> generated_file_path
        """
        if not jobs:
            return {}

        if not self.indextts_dir:
            logger.warning("INDEXTTS_DIR is not set. Skipping IndexTTS clone batch.")
            return {}

        indextts_dir = self.indextts_dir
        config_path = indextts_dir / "checkpoints" / "config.yaml"
        model_dir = indextts_dir / "checkpoints"
        runner_path = Path(__file__).resolve().parent / "indextts_batch_runner.py"

        if not runner_path.exists():
            logger.error(f"IndexTTS batch runner not found at {runner_path}")
            return {}
        if not config_path.exists():
            logger.error(f"IndexTTS config not found at {config_path}")
            return {}

        jobs_file = output_dir / "indextts_jobs.json"
        try:
            with open(jobs_file, "w", encoding="utf-8") as f:
                json.dump({"jobs": jobs}, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to write IndexTTS job file: {e}")
            return {}

        cmd = [
            sys.executable,
            str(runner_path),
            "--jobs", str(jobs_file),
            "--config", str(config_path),
            "--model_dir", str(model_dir),
            "--device", "cuda" if torch.cuda.is_available() else "cpu",
        ]

        if torch.cuda.is_available():
            cmd.append("--fp16")

        env = os.environ.copy()
        ffmpeg_dir = str(Path(__file__).resolve().parent.parent.parent / "tools" / "ffmpeg")
        env["PATH"] = ffmpeg_dir + os.pathsep + env.get("PATH", "")
        # Critical: add indextts_dir to PYTHONPATH so the subprocess can import `indextts`
        env["PYTHONPATH"] = str(indextts_dir) + os.pathsep + env.get("PYTHONPATH", "")
        hf_cache_root = str(model_dir / "hf_cache")
        env.setdefault("HF_HOME", hf_cache_root)
        env.setdefault("HUGGINGFACE_HUB_CACHE", hf_cache_root)
        env.setdefault("TRANSFORMERS_CACHE", hf_cache_root)
        env.setdefault("HF_HUB_CACHE", hf_cache_root)
        env.setdefault("HF_HUB_OFFLINE", "1")

        try:
            logger.info(f"🧬 Batch cloning {len(jobs)} segments with one IndexTTS process...")
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(indextts_dir),
                env=env,
            )
            stdout, stderr = await proc.communicate()
            out_text = stdout.decode(errors="ignore").strip()
            err_text = stderr.decode(errors="ignore").strip()

            if proc.returncode != 0:
                logger.error(f"IndexTTS batch failed: {err_text or out_text}")
                return {}

            if not out_text:
                logger.error("IndexTTS batch returned empty output.")
                return {}

            summary = json.loads(out_text.splitlines()[-1])
            ok_map = {}
            for item in summary.get("results", []):
                if item.get("ok"):
                    idx = int(item.get("index"))
                    path = item.get("output_path")
                    if path and Path(path).exists():
                        ok_map[idx] = path

            logger.info(f"✅ IndexTTS batch done: {len(ok_map)}/{len(jobs)}")
            return ok_map
        except Exception as e:
            logger.error(f"IndexTTS batch invocation failed: {e}")
            return {}
        finally:
            try:
                if jobs_file.exists():
                    jobs_file.unlink()
            except Exception:
                pass


    async def generate_cloned_audio(self, text: str, output_file: Path, ref_audio_path: Path) -> Optional[str]:
        """
        Generate TTS using IndexTTS (Zero-shot Cloning).
        """
        # Call the CLI script as a subprocess to keep environment isolated and simple
        # python d:\vid\index-tts-main\indextts\cli.py -v ref -o out "text"
        
        if not self.indextts_dir:
            logger.warning("INDEXTTS_DIR is not set. Skipping IndexTTS single clone.")
            return None

        indextts_dir = self.indextts_dir
        cli_path = indextts_dir / "indextts" / "cli.py"
        config_path = indextts_dir / "checkpoints" / "config.yaml"
        model_dir = indextts_dir / "checkpoints"
        
        if not cli_path.exists():
            logger.error(f"IndexTTS CLI not found at {cli_path}")
            return None
        
        if not config_path.exists():
            logger.error(f"IndexTTS config not found at {config_path}")
            return None
            
        cmd = [
             sys.executable, str(cli_path),
             "-v", str(ref_audio_path),
             "-o", str(output_file),
             "-c", str(config_path),
             "--model_dir", str(model_dir),
             "-d", "cuda" if torch.cuda.is_available() else "cpu",  # Auto-detect GPU (RTX 5070 8GB should fit)
             "-f",  # Force overwrite
             text
        ]

        try:
             logger.info(f"🧬 Cloning [{text[:10]}...] using {ref_audio_path.name}")
             # Inject FFmpeg shared libs into subprocess PATH so librosa/soundfile can load audio
             env = os.environ.copy()
             ffmpeg_dir = str(Path(__file__).resolve().parent.parent.parent / "tools" / "ffmpeg")
             env["PATH"] = ffmpeg_dir + os.pathsep + env.get("PATH", "")
             # Critical: add indextts_dir to PYTHONPATH so the subprocess can import `indextts`
             env["PYTHONPATH"] = str(indextts_dir) + os.pathsep + env.get("PYTHONPATH", "")
             hf_cache_root = str(model_dir / "hf_cache")
             env.setdefault("HF_HOME", hf_cache_root)
             env.setdefault("HUGGINGFACE_HUB_CACHE", hf_cache_root)
             env.setdefault("TRANSFORMERS_CACHE", hf_cache_root)
             env.setdefault("HF_HUB_CACHE", hf_cache_root)
             env.setdefault("HF_HUB_OFFLINE", "1")
             proc = await asyncio.create_subprocess_exec(
                 *cmd,
                 stdout=asyncio.subprocess.PIPE,
                 stderr=asyncio.subprocess.PIPE,
                 cwd=str(indextts_dir),  # Run from IndexTTS directory
                 env=env
             )
             stdout, stderr = await proc.communicate()
             
             if proc.returncode != 0:
                 error_msg = stderr.decode().strip() or stdout.decode().strip()
                 logger.error(f"IndexTTS Error: {error_msg}")
                 return None
                 
             if output_file.exists() and output_file.stat().st_size > 0:
                 return str(output_file)
             else:
                 logger.error("IndexTTS finished but output file missing/empty.")
                 return None
                 
        except Exception as e:
            logger.error(f"IndexTTS invocation failed: {e}")
            return None

    def _run_edge_tts_sync(self, text: str, output_file_str: str, voice: str) -> bool:
        """
        Run Edge-TTS in a fresh event loop (isolated from main asyncio loop).
        This prevents 'cannot schedule new futures after shutdown' errors.
        """
        async def _generate():
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(output_file_str)
        
        # Create a brand new event loop for each TTS call
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_generate())
            return True
        except Exception as e:
            raise e
        finally:
            loop.close()

    async def generate_audio(self, text: str, output_file: Path, voice: str) -> Optional[str]:
        """
        Generate TTS using Edge-TTS with retry logic.
        Uses isolated event loop to prevent shutdown issues.
        """
        output_file_str = str(output_file)
        
        # Retry up to 3 times
        for attempt in range(3):
            try:
                # Run in dedicated thread pool with isolated event loop
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(
                    self._tts_executor,  # Use dedicated executor (not default which may be shut down)
                    self._run_edge_tts_sync,
                    text,
                    output_file_str,
                    voice
                )
                
                if os.path.exists(output_file_str) and os.path.getsize(output_file_str) > 0:
                    return output_file_str
                
            except Exception as e:
                logger.warning(f"TTS Attempt {attempt+1}/3 failed for '{text[:10]}...': {e}")
                await asyncio.sleep(1) # Backoff
        
        logger.error(f"TTS Failed after 3 attempts for: {text[:20]}...")
        return None

    async def dub_segments(self, segments: List[dict], output_dir: Path, voice: str = "zh-CN-XiaoxiaoNeural", original_audio_path: Path = None) -> Path:
        """
        Generates audio for each segment and merges them with proper synchronization.
        Uses Speaker Diarization + Voice Cloning if 'original_audio_path' is provided.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        final_audio_path = output_dir / "final_dub.wav" # Changed in memory, consistency check
        
        # Build a fixed timeline to avoid cumulative drift (better lip-sync)
        timeline_ms = int(max((s.get('end', 0) for s in segments), default=0) * 1000) + 500
        combined_audio = AudioSegment.silent(duration=max(1000, timeline_ms), frame_rate=24000)
        
        logger.info(f"Generating dub using voice: {voice}")
        
        # Pre-process Speakers for Reference Audio
        speaker_refs = {}
        if original_audio_path and original_audio_path.exists():
            from services.audio_processor import audio_processor
            
            # Find the best (longest) segment for each speaker to use as reference
            speakers = set(s.get('speaker', 'SPEAKER_00') for s in segments)
            for spk in speakers:
                # Find all segments for this speaker
                spk_segs = [s for s in segments if s.get('speaker') == spk]
                if not spk_segs: continue

                # Prefer clean-like segments close to 8s
                # Heuristic: non-empty text, moderate duration range, closest to 8s
                target_ref_dur = 8.0
                candidates = []
                for seg in spk_segs:
                    seg_text = (seg.get('text') or '').strip()
                    seg_dur = seg.get('end', 0) - seg.get('start', 0)
                    if len(seg_text) < 4:
                        continue
                    if 2.0 <= seg_dur <= 12.0:
                        candidates.append(seg)

                if candidates:
                    best_seg = min(candidates, key=lambda x: abs((x['end'] - x['start']) - target_ref_dur))
                else:
                    best_seg = max(spk_segs, key=lambda x: x['end'] - x['start'])

                duration = best_seg['end'] - best_seg['start']

                if duration > 1.0: # Minimum 1s needed for cloning
                    ref_path = output_dir / f"ref_{spk}.wav"
                    try:
                        audio_processor.cut_audio_segment(
                            original_audio_path, 
                            best_seg['start'], 
                            best_seg['end'], 
                            ref_path
                        )
                        speaker_refs[spk] = ref_path
                        logger.info(f"🎤 Extracted reference audio for {spk}: {ref_path}")
                    except Exception as e:
                        logger.warning(f"Failed to extract reference for {spk}: {e}")

        # Pre-generate clone candidates in one batch to avoid reloading IndexTTS models per segment
        clone_jobs = []
        for i, doc in enumerate(segments):
            text = doc.get('text', '')
            speaker = doc.get('speaker', 'SPEAKER_00')
            if not text or not text.strip():
                continue
            if speaker in speaker_refs:
                clone_jobs.append({
                    "index": i,
                    "text": text,
                    "voice": str(speaker_refs[speaker]),
                    "output_path": str(output_dir / f"seg_{i:03d}.wav"),
                })

        max_clone_segments = int(os.getenv("INDEXTTS_MAX_BATCH_SEGMENTS", "999999"))
        if max_clone_segments <= 0:
            if clone_jobs:
                logger.info("IndexTTS cloning disabled by INDEXTTS_MAX_BATCH_SEGMENTS<=0. Using EdgeTTS for all segments.")
            clone_jobs = []
        elif len(clone_jobs) > max_clone_segments:
            logger.warning(
                f"Clone jobs too many ({len(clone_jobs)}). Limiting to first {max_clone_segments}; remaining segments use EdgeTTS."
            )
            clone_jobs = clone_jobs[:max_clone_segments]

        clone_candidate_indices = {job["index"] for job in clone_jobs}

        clone_generated_map = await self.generate_cloned_audio_batch(clone_jobs, output_dir) if clone_jobs else {}

        success_count = 0
        for i, doc in enumerate(segments):
            text = doc['text']
            speaker = doc.get('speaker', 'SPEAKER_00')
            
            if not text or not text.strip():
                continue

            seg_file = output_dir / f"seg_{i:03d}.wav" # Changed to wav for better compatibility
            
            # DECISION: Clone or Default?
            generated_file = None
            
            # 1. Prefer pre-generated clone result
            if i in clone_generated_map:
                generated_file = clone_generated_map[i]

            # 2. Fallback to per-segment clone (safety path)
            elif speaker in speaker_refs and i in clone_candidate_indices:
                logger.info(f"Attempting single clone fallback for {speaker}...")
                generated_file = await self.generate_cloned_audio(text, seg_file, speaker_refs[speaker])

            # 3. Fallback to EdgeTTS
            if not generated_file:
                if speaker in speaker_refs:
                    logger.warning(f"Cloning failed for {speaker}, falling back to EdgeTTS.")
                
                # Basic Voice Mapping for speakers if we had different Edge Voices
                # For now, just use the global default
                generated_file = await self.generate_audio(text, seg_file, voice)
            
            if generated_file:
                try:
                    clip = AudioSegment.from_file(str(generated_file))
                    success_count += 1
                    
                    target_start_ms = int(doc['start'] * 1000)
                    target_end_ms = int(doc['end'] * 1000)
                    target_duration = max(100, target_end_ms - target_start_ms)

                    # Avoid hard truncation that can cut words mid-sentence.
                    # Only guard against extremely long outliers.
                    if len(clip) > int(target_duration * 3.5):
                        clip = clip[:int(target_duration * 3.5)]

                    # Smooth boundaries for better naturalness
                    if len(clip) > 120:
                        clip = clip.fade_in(20).fade_out(120)

                    # Overlay at absolute timestamp (no cumulative offset drift)
                    combined_audio = combined_audio.overlay(clip, position=max(0, target_start_ms))
                    
                except Exception as e:
                    logger.error(f"Failed to process clip {seg_file}: {e}")
            else:
                logger.warning(f"Skipping segment {i} due to TTS failure.")

        if success_count == 0:
            logger.error("No TTS segments were generated successfully!")
            # Save at least 1 second of silence to avoid ffmpeg error
            combined_audio = AudioSegment.silent(duration=1000, frame_rate=24000)
        
        # Consolidate format before export
        combined_audio = combined_audio.set_frame_rate(24000).set_channels(1)
        
        # Export as WAV separately
        combined_audio.export(str(final_audio_path), format="wav")
        logger.success(f"Dubbing complete: {final_audio_path}")
        
        return final_audio_path

tts_service = TTSService()
