# Vows (VoxFlow Open-Source Package)

一个可复现的视频配音流水线（音频提取 -> 人声分离 -> ASR+说话人分离 -> 翻译 -> TTS 克隆/回退 -> 混音导出）。

本目录是为 GitHub 发布整理后的安全版本：
- 已移除运行产物、上传素材、模型权重、缓存。
- 已移除明文密钥（请使用 `backend/.env.example` 自行配置）。
- 已补充部署、使用、合规说明文档。

## 文档导航
- 部署步骤：`docs/DEPLOYMENT_ZH.md`
- 使用步骤：`docs/USAGE_ZH.md`
- 文件说明：`docs/FILES_ZH.md`
- 合规与许可证：`docs/COMPLIANCE_ZH.md`
- GitHub发布：`docs/GITHUB_RELEASE_ZH.md`

## 目录结构（关键）
- `backend/` 后端 FastAPI + 流水线服务
- `frontend/` 前端页面（Vite）
- `tools/` 调试与工具脚本
- `run_task.py` / `run_task_with_subtitles.py` 任务触发脚本
- `一键处理视频.bat` / `一键处理视频并加硬字幕.bat` Windows 一键脚本

## 快速开始（摘要）
1. 安装 Python 3.10+、FFmpeg、Node.js（如果运行前端）。
2. 复制 `backend/.env.example` 为 `backend/.env` 并填入密钥。
3. 准备并配置 `INDEXTTS_DIR`（指向本机 index-tts-main 代码目录）。
4. 安装后端依赖并启动：`python backend/app.py`。
5. 使用脚本上传视频并轮询任务状态。

详细命令见 `docs/DEPLOYMENT_ZH.md` 与 `docs/USAGE_ZH.md`。

## 发布前检查
- 确认仓库中没有 `.env`、没有 token、没有个人音视频素材。
- 确认未上传 `models/`、`checkpoints/`、`hf_cache/`。
- 确认 README 和合规文档完整。

## 免责声明
本项目仅用于合法合规的技术研究与工程实践。使用者应自行承担素材授权、模型许可、数据合规等责任。
