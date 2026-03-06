# Vows (VoxFlow Open-Source Package)

✨🎬🌍🚀 A reproducible AI video dubbing pipeline.

Languages: [简体中文](README.md) · [English](README_EN.md) · [日本語](README_JA.md)


## 项目简介

Vows 是一个面向“不同语言的视频同声翻译配音”的工程化流水线，目标是把“输入一个原视频”变成“输出一个可发布的目标语言（50种语言）版本视频”。  
它不是单一模型推理脚本，而是一套可复现、可回退、可扩展的完整流程系统。

核心能力：

1. 自动抽取视频音频并进行人声分离（降背景干扰）
2. ASR + 说话人分离（按时间轴和角色组织文本）
3. LLM 翻译（分段翻译，失败可回退原文）
4. IndexTTS 声音克隆（失败自动回退 EdgeTTS）
5. 时间轴对齐混音导出（可选硬字幕烧录）
6. 支持脚本化、API化、一键 bat 拖拽运行

一句话总结：

音频提取 -> 人声分离 -> ASR+说话人分离 -> LLM翻译 -> TTS克隆/回退 -> 混音导出

---

## 效果对比


### 案例 1：TED（带硬字幕）
- 原视频：



https://github.com/user-attachments/assets/6d045aa6-6eec-4c29-8a7f-918809bea939




- 结果视频：




https://github.com/user-attachments/assets/ead60688-c0de-4ee9-983d-e3d9af182b16




对比要点：
1. 保留原视频节奏与时序，配音按片段时间轴对齐
2. 输出为目标语言配音，并带可视字幕
3. 语音风格接近参考音色，失败片段自动回退避免整段中断

### 案例 2：Trump（不带字幕）
- 原视频：




https://github.com/user-attachments/assets/b396c851-d8c8-44a2-ba6f-4cba41926812



- 结果视频：




https://github.com/user-attachments/assets/7b0c1728-c79d-4841-9d07-616031f63096




对比要点：
1. 只输出配音视频，不烧录字幕
2. 背景音与人声关系保持自然（以最终混音结果为准）
3. 在翻译/克隆某一步出现异常时，系统有回退策略，整体任务仍可完成

---


## 文档导航

1. 文件说明：`docs/FILES_ZH.md`
2. 合规说明：`docs/COMPLIANCE_ZH.md`


---

## 1. 环境要求（Windows）

1. OS：Windows 10/11
2. Python：3.10 或 3.11
3. Conda：推荐（Anaconda/Miniconda 均可）
4. CUDA：可选（有 NVIDIA GPU 推荐）
5. FFmpeg：系统 PATH 可用，或放在 `tools/ffmpeg`
6. Node.js：仅前端需要（建议 Node 18+）

---

## 2. 拉取代码

```powershell
git clone https://github.com/wkl1918/Vows
cd Vows
```

---

## 3. 创建后端环境并安装依赖

```powershell
conda create -n VoxFlow python=3.10 -y
conda activate VoxFlow
pip install -r backend/requirements.txt
```

---

## 4. 准备 IndexTTS2（单独仓库）

本仓库不分发 IndexTTS 权重和缓存。请按上游仓库准备：

1. 推荐官方仓库：`https://github.com/index-tts/index-tts`
2. 克隆后得到本地目录，例如：`D:\AI\index-tts-main`
按 Windows 给你一套可直接照抄的做法。

3. 下载 `checkpoints` 与依赖（详细步骤）

### 方案A（推荐）：用 HuggingFace CLI 下载
在 VoxFlow 环境里执行：

```powershell
conda activate VoxFlow
pip install -U "huggingface_hub[cli]"
```

先准备目录（示例放在 `D:\AI\index-tts-main`）：

```powershell
mkdir D:\AI -Force
cd D:\AI
git clone https://github.com/index-tts/index-tts.git index-tts-main
cd index-tts-main
```

下载模型到 `checkpoints`：

```powershell
hf download IndexTeam/IndexTTS-2 --local-dir checkpoints
```

如果你在国内访问慢，可以先设镜像再下载：

```powershell
$env:HF_ENDPOINT="https://hf-mirror.com"
hf download IndexTeam/IndexTTS-2 --local-dir checkpoints
```

---


你可以直接检查：

```powershell
Test-Path D:\AI\index-tts-main\checkpoints\config.yaml
Test-Path D:\AI\index-tts-main\checkpoints\gpt.pth
Test-Path D:\AI\index-tts-main\checkpoints\s2mel.pth
```

都返回 `True` 才算完整。

---

4. 在 .env 配置 `INDEXTTS_DIR`

打开 `D:\Vows\backend\.env`，加/改这一行：

```env
INDEXTTS_DIR=D:/AI/index-tts-main
```

注意：
1. 用你自己的实际路径。
2. 推荐用 `/`，Windows 也能识别。
3. 不要写到 `checkpoints`，要写到 **index-tts-main 根目录**。

---

5.配完后快速验证

启动后端前执行：

```powershell
python -c "import os; p=os.getenv('INDEXTTS_DIR'); print('INDEXTTS_DIR=',p)"
```

然后启动后端看日志，正常会在克隆阶段不再报 `IndexTTS config not found`。

如果你愿意，我可以下一条给你一个“一键自检命令”，一次性检查 .env、`INDEXTTS_DIR`、`checkpoints` 是否都就绪。

---

## 5. 配置环境变量

先复制模板：

```powershell
Copy-Item backend/.env.example backend/.env
```

然后编辑 `backend/.env`，至少配置以下项：

```env
HF_TOKEN=hf_xxx
LLM_API_KEY=sk-xxx
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
INDEXTTS_DIR=D:/AI/index-tts-main
```

说明：
1. `HF_TOKEN`：用于 pyannote / huggingface 资源访问的，可在 huggingface申请。
2. `LLM_API_KEY`：用于翻译（千问/DeepSeek/OpenAI 兼容接口均可）。
3. `INDEXTTS_DIR`：本机 IndexTTS 代码目录路径。
4. 如果不配置 `INDEXTTS_DIR`，系统会跳过克隆并回退 EdgeTTS。

如需代理，可在 `.env` 添加：
```env
HTTP_PROXY=http://127.0.0.1:7897
HTTPS_PROXY=http://127.0.0.1:7897
```

---

## 6. 启动后端

```powershell
conda activate VoxFlow
cd backend
python app.py
```

成功标志：

`Uvicorn running on http://127.0.0.1:8000`

---

## 7. 启动前端（可选）

```powershell
cd frontend
npm install
npm run dev
```

---

## 8. 运行方式

以后你切换语言就 3 种方式，选你最顺手的：

### 8.1 前端方式（最简单）
1. 启动后端：`python backend/app.py`
2. 启动前端：`cd frontend && npm install && npm run dev`
3. 页面里先选“目标语言（50选1）”，再上传视频

适合：可视化操作，不想记命令。

### 8.2 拖拽 bat 方式（傻瓜式）
1. 直接拖视频到：
- 一键处理视频.bat（不烧录硬字幕）
- 一键处理视频并加硬字幕.bat（烧录硬字幕）
2. 如果你没传第二参数，它会弹出 50 语言代码提示让你选。
3. 也可以直接命令行传语言：

```powershell
一键处理视频.bat "D:\demo.mp4" en
一键处理视频并加硬字幕.bat "D:\demo.mp4" ja
```

### 8.3 Python 脚本方式（最可控）
```powershell
python run_task.py "D:/path/to/input.mp4" zh
python run_task_with_subtitles.py "D:/path/to/input.mp4" ja
```

第二个参数就是目标语言代码，不传默认 `zh`。

---

常用语言代码（你现在支持 50 个）：
- `zh` 中文
- `en` 英文
- `ja` 日文
- `ko` 韩文
- `es` 西班牙语
- `fr` 法语
- `de` 德语
- `ru` 俄语
- `it` 意大利语
- `pt` 葡萄牙语
- `ar` 阿拉伯语
- `hi` 印地语
- `th` 泰语
- `vi` 越南语
- `tr` 土耳其语
- `nl` 荷兰语
- `pl` 波兰语
- `id` 印尼语
- `ms` 马来语
- `fa` 波斯语
- `uk` 乌克兰语
- `cs` 捷克语
- `sk` 斯洛伐克语
- `hu` 匈牙利语
- `ro` 罗马尼亚语
- `bg` 保加利亚语
- `hr` 克罗地亚语
- `sl` 斯洛文尼亚语
- `sr` 塞尔维亚语
- `da` 丹麦语
- `sv` 瑞典语
- `no` 挪威语
- `fi` 芬兰语
- `et` 爱沙尼亚语
- `lv` 拉脱维亚语
- `lt` 立陶宛语
- `el` 希腊语
- `he` 希伯来语
- `bn` 孟加拉语
- `ta` 泰米尔语
- `te` 泰卢固语
- `mr` 马拉地语
- `gu` 古吉拉特语
- `kn` 卡纳达语
- `ml` 马拉雅拉姆语
- `ur` 乌尔都语
- `sw` 斯瓦希里语
- `af` 南非语
- `fil` 菲律宾语
- `ca` 加泰罗尼亚语
补一句关键点：如果翻译接口失败，系统会回退原文，所以看起来会“语言没变”；这时先检查 `LLM_API_KEY` 和网络/代理是否正常。

---

## 9. 流程与回退策略

1. 音频提取：从视频抽取原始音频
2. 人声分离：Demucs 分离 vocals
3. 语音识别：Whisper 转写
4. 说话人分离：Pyannote diarization
5. 翻译：LLM 分段翻译
6. 克隆：IndexTTS 批量合成
7. 回退：克隆失败时自动降级为 EdgeTTS
8. 混音导出：按时间轴叠加生成最终音频/视频

---

## 10. 输出文件位置

默认输出在：

`backend/storage/outputs/<task_id>/`

常见文件：
1. `final_<源视频名>.mp4`：合成结果
2. `final_<源视频名>.srt`：字幕文件（如启用）
3. `final_<源视频名>_subtitled.mp4`：硬字幕成片（如启用）

---

## 11. 常见问题排查（结合实战日志）

## 11.1 ASR 下载失败（ProxyError / 127.0.0.1:7897）

现象：
`Failed to establish a new connection: [WinError 10061]`

原因：
代理变量启用了，但本地代理程序未运行。

处理：
1. 启动代理程序，确保端口有效。
2. 或删除/注释 `HTTP_PROXY` 和 `HTTPS_PROXY`。
3. 重新启动后端再试。

## 11.2 LLM 翻译失败（SSL EOF）

现象：
`SSLEOFError: EOF occurred in violation of protocol`

原因：
网络链路/TLS/代理问题导致请求中断。

处理：
1. 检查代理与网络。
2. 更换网络环境再试。
3. 失败时系统会回退原文，导致输出仍是原语言（这是预期行为）。

## 11.3 “为什么生成的是英文，不是中文”

核心原因：
翻译阶段失败并回退原文。

排查顺序：
1. 看日志是否有 `LLM Translation failed`
2. 检查 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`
3. 检查代理与外网可达性

## 11.4 克隆阶段卡住或无 wav 输出

排查：
1. 确认 `.env` 中 `INDEXTTS_DIR` 正确
2. 确认 `INDEXTTS_DIR/checkpoints/config.yaml` 存在
3. 确认后端环境依赖完整（librosa/soundfile/torch）
4. 查看日志是否出现 IndexTTS 子进程错误

## 11.5 后端启动脚本只显示 `Active code page: 65001`

常见原因：
工作目录不正确或环境未激活。

处理：
1. 使用当前仓库提供的一键脚本，不要改成旧版复杂 `start` 命令拼接。
2. 确保项目目录结构完整，`_start_backend.bat` 存在。

---

## 12. 性能与质量建议

1. GPU：优先 CUDA，速度提升明显。
2. 参考音频：单人、干净、无背景音乐、5-15秒。
3. 文本切分：长段落分句有助于稳定性。
4. 批量克隆：保持默认批处理方式，避免频繁重复加载模型。
5. 显存不足：降低并发，或暂时切 CPU 路径验证流程。

---

## 13. 安全与合规（重点）

1. 禁止上传真实密钥（`.env`、token、API key）。
2. 禁止上传用户私有音视频与未授权素材。
3. 本仓库不分发上游模型权重，使用者需自行下载并遵循上游许可。
4. 使用 IndexTTS2 时，请遵循其官方许可证与免责声明。
5. 语音克隆请确保拥有被克隆声音的合法授权。

---



## 14. 致谢与上游引用

1. IndexTTS / IndexTTS2 官方仓库与论文
2. Demucs / Whisper / Pyannote / EdgeTTS 等开源组件
3. 详见 `THIRD_PARTY_NOTICES.md`

---

## 免责声明

本项目仅用于合法合规的技术研究与工程实践。使用者应自行承担素材授权、模型许可、数据合规与内容合规责任。
```

