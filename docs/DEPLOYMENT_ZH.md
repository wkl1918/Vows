# 部署步骤（Windows）

## 1. 环境要求
- OS: Windows 10/11
- Python: 3.10 或 3.11
- CUDA: 可选（有 NVIDIA GPU 推荐）
- FFmpeg: 需可用（项目会从 `tools/ffmpeg` 或系统 PATH 读取）
- Node.js: 仅在运行前端时需要

## 2. 拉取代码
```powershell
git clone <your-repo-url> Vows
cd Vows
```

## 3. 创建 Python 环境并安装后端依赖
```powershell
conda create -n VoxFlow python=3.10 -y
conda activate VoxFlow
pip install -r backend/requirements.txt
```

## 4. 配置环境变量
复制模板：
```powershell
Copy-Item backend/.env.example backend/.env
```
填写至少以下项：
- `HF_TOKEN`：用于 pyannote / huggingface 资源访问
- `LLM_API_KEY`：用于翻译
- `INDEXTTS_DIR`：本机 `index-tts-main` 代码目录

说明：
- 若未配置 `INDEXTTS_DIR`，后端会跳过克隆并回退到 EdgeTTS（仍可跑通流程，但不是声音克隆）。
- 一键 bat 脚本已支持自动探测常见 Conda 路径（`%USERPROFILE%\anaconda3` / `miniconda3` / `%ProgramData%\anaconda3`）。

如网络需要代理，打开 `backend/.env` 中代理项。

## 5. 准备 IndexTTS（单独仓库）
本仓库不包含 IndexTTS 权重和缓存，请按官方说明准备：
1. 克隆 `index-tts-main`
2. 下载其依赖模型与 `checkpoints`
3. 确保 `INDEXTTS_DIR` 指向该目录

## 6. 启动后端
```powershell
conda activate VoxFlow
cd backend
python app.py
```
成功标志：
- `Uvicorn running on http://127.0.0.1:8000`

## 7. 启动前端（可选）
```powershell
cd frontend
npm install
npm run dev
```

## 8. 常见故障
## ASR 下载失败（ProxyError 127.0.0.1:7897）
- 说明代理变量仍生效但代理程序没开。
- 处理：清除 `HTTP_PROXY/HTTPS_PROXY` 或启动本地代理。

## LLM 翻译失败（SSL EOF）
- 说明到 DashScope 的 TLS 链路异常。
- 处理：检查网络、代理、企业证书；必要时更换网络。

## 克隆阶段无 wav 输出
- 确认 `INDEXTTS_DIR` 正确
- 确认 `INDEXTTS_DIR/checkpoints/config.yaml` 存在
- 确认后端环境中安装了音频相关依赖（librosa/soundfile）
