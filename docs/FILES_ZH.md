# 文件说明

## 根目录
- `README.md`：项目总览与入口
- `.gitignore`：GitHub 忽略规则（密钥/模型/产物）
- `_start_backend.bat`：后台启动辅助脚本
- `run_task.py`：标准任务触发脚本
- `run_task_with_subtitles.py`：带硬字幕流程脚本

## backend/
- `app.py`：FastAPI 入口
- `requirements.txt`：后端依赖
- `.env.example`：环境变量模板（请复制为 `.env`）
- `api/tasks.py`：任务上传、状态接口
- `services/asr_service.py`：ASR 与 diarization
- `services/llm_service.py`：翻译服务
- `services/tts_service.py`：克隆与 TTS 合成
- `services/audio_processor.py`：音频处理

## frontend/
- 前端页面和构建配置（Vite + TS）

## tools/
- 调试和辅助工具脚本

## 明确不包含
- `models/`, `checkpoints/`, `hf_cache/` 等大模型权重
- `backend/storage/outputs`, `uploads` 等运行产物
- 任意密钥文件与个人素材
