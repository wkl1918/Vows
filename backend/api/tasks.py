from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
import shutil
import os
import traceback
import asyncio
from pathlib import Path
from typing import List

from core.config import UPLOAD_DIR, TEMP_DIR, OUTPUT_DIR
from schemas.task import TaskCreate, TaskResponse, TaskStatus
from services.task_manager import TaskManager
from services.audio_processor import audio_processor
from services.asr_service import asr_service
from services.llm_service import llm_service
from services.tts_service import tts_service

router = APIRouter()

def run_pipeline(task_id: str, file_path: Path):
    # Need to run async code inside this sync thread wrapper
    asyncio.run(run_pipeline_async(task_id, file_path))

async def run_pipeline_async(task_id: str, file_path: Path):
    try:
        task = TaskManager.get_task(task_id)
        if not task:
            return

        # 1. Extract Audio
        TaskManager.update_status(task_id, TaskStatus.PROCESSING, 10, "Extracting Audio...")
        
        audio_filename = f"{task.id}_full.wav"
        full_audio_path = TEMP_DIR / audio_filename
        
        audio_processor.extract_audio(file_path, full_audio_path)
        
        # 2. Separate Vocals
        TaskManager.update_status(task_id, TaskStatus.PROCESSING, 25, "Separating Vocals (Demucs)...")
        
        # Demucs creates its own folder structure inside output_dir
        demucs_out_dir = TEMP_DIR / "demucs"
        vocals_path, bgm_path = audio_processor.separate_vocals(full_audio_path, demucs_out_dir)
        
        # 3. Transcribe
        TaskManager.update_status(task_id, TaskStatus.PROCESSING, 45, "Transcribing Vocals...")
        
        segments = asr_service.transcribe(vocals_path, language=task.original_language)
        
        # 4. Translate (LLM)
        TaskManager.update_status(task_id, TaskStatus.PROCESSING, 65, "Translating Text (LLM)...")
        translated_segments = llm_service.translate_segments(segments, task.target_language)
        
        # 5. Dubbing (TTS)
        TaskManager.update_status(task_id, TaskStatus.PROCESSING, 80, "Generating Speech (TTS)...")
        dub_dir = OUTPUT_DIR / task_id / "dub"
        
        # Voice Mapping
        voice_map = {
            "zh": "zh-CN-XiaoxiaoNeural",
            "en": "en-US-AriaNeural",
            "ja": "ja-JP-NanamiNeural",
            "ko": "ko-KR-SunHiNeural",
            "es": "es-ES-ElviraNeural",
            "fr": "fr-FR-DeniseNeural",
            "de": "de-DE-KatjaNeural",
            "ru": "ru-RU-SvetlanaNeural",
            "it": "it-IT-ElsaNeural",
            "pt": "pt-BR-FranciscaNeural",
            "ar": "ar-SA-ZariyahNeural",
            "hi": "hi-IN-SwaraNeural",
            "th": "th-TH-PremwadeeNeural",
            "vi": "vi-VN-HoaiMyNeural",
            "tr": "tr-TR-EmelNeural",
            "nl": "nl-NL-ColetteNeural",
            "pl": "pl-PL-ZofiaNeural",
            "id": "id-ID-GadisNeural",
            "ms": "ms-MY-YasminNeural",
            "fa": "fa-IR-DilaraNeural",
            "uk": "en-US-AriaNeural",
            "cs": "en-US-AriaNeural",
            "sk": "en-US-AriaNeural",
            "hu": "en-US-AriaNeural",
            "ro": "en-US-AriaNeural",
            "bg": "en-US-AriaNeural",
            "hr": "en-US-AriaNeural",
            "sl": "en-US-AriaNeural",
            "sr": "en-US-AriaNeural",
            "da": "en-US-AriaNeural",
            "sv": "en-US-AriaNeural",
            "no": "en-US-AriaNeural",
            "fi": "en-US-AriaNeural",
            "et": "en-US-AriaNeural",
            "lv": "en-US-AriaNeural",
            "lt": "en-US-AriaNeural",
            "el": "en-US-AriaNeural",
            "he": "en-US-AriaNeural",
            "bn": "en-US-AriaNeural",
            "ta": "en-US-AriaNeural",
            "te": "en-US-AriaNeural",
            "mr": "en-US-AriaNeural",
            "gu": "en-US-AriaNeural",
            "kn": "en-US-AriaNeural",
            "ml": "en-US-AriaNeural",
            "ur": "en-US-AriaNeural",
            "sw": "en-US-AriaNeural",
            "af": "en-US-AriaNeural",
            "fil": "en-US-AriaNeural",
            "ca": "en-US-AriaNeural",
        }
        selected_voice = voice_map.get(task.target_language, "zh-CN-XiaoxiaoNeural")
        
        # Pass vocals_path for reference audio extraction (IndexTTS)
        final_dub_audio = await tts_service.dub_segments(
            translated_segments, 
            dub_dir, 
            voice=selected_voice,
            original_audio_path=vocals_path
        )

        # 6. Merge Video + Audio
        if final_dub_audio and final_dub_audio.exists():
            TaskManager.update_status(task_id, TaskStatus.PROCESSING, 95, "Merging Video & Audio...")
            
            final_video_path = OUTPUT_DIR / task_id / f"final_{task.filename}"
            # Ensure bgm_path exists (it was returned by separate_vocals)
            
            try:
                audio_processor.merge_video_audio(
                    video_path=file_path,
                    dub_audio_path=final_dub_audio,
                    bgm_audio_path=bgm_path,
                    output_path=final_video_path
                )
                TaskManager.update_status(task_id, TaskStatus.COMPLETED, 100, f"Done! Created {final_video_path.name}")
            except Exception as e:
                TaskManager.update_status(task_id, TaskStatus.FAILED, 99, f"Merge failed: {e}")
        else:
            TaskManager.update_status(task_id, TaskStatus.FAILED, 90, "TTS failed to produce audio.")

    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}"
        print(f"❌ Task {task_id} Error: {traceback.format_exc()}")
        TaskManager.update_status(task_id, TaskStatus.FAILED, 0, error_msg)



@router.post("/upload", response_model=TaskResponse)
def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    target_language: str = "zh"
):
    print(f"📥 Received upload request for file: {file.filename}")
    # 1. Save file
    safe_filename = file.filename.replace(" ", "_").replace(":", "")
    file_path = UPLOAD_DIR / safe_filename
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Create Task
    task_in = TaskCreate(filename=safe_filename, target_language=target_language)
    task = TaskManager.create_task(task_in)
    
    # 3. Trigger Background Processing (Async)
    background_tasks.add_task(run_pipeline, task.id, file_path)
    
    return task

@router.get("/{task_id}", response_model=TaskResponse)
def get_task_status(task_id: str):
    task = TaskManager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.get("/", response_model=List[TaskResponse])
def list_tasks():
    return TaskManager.list_tasks()
