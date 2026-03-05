# 使用说明

## 1. 一键脚本（Windows）
- `一键处理视频.bat`：处理视频并生成配音（不硬烧字幕）
- `一键处理视频并加硬字幕.bat`：处理视频并写入硬字幕

使用方式：将视频文件拖拽到对应 bat 文件上。

## 2. 命令行方式
## 2.1 启动后端
```powershell
conda activate VoxFlow
cd backend
python app.py
```

## 2.2 运行任务脚本
```powershell
cd ..
python run_task.py "D:/path/to/input.mp4"
```
或
```powershell
python run_task_with_subtitles.py "D:/path/to/input.mp4"
```

## 3. 流程阶段说明
1. 抽取音频
2. Demucs 分离人声
3. Whisper ASR + Pyannote 说话人分离
4. LLM 翻译（失败时会回退原文）
5. IndexTTS 克隆（失败时回退 EdgeTTS）
6. 合并导出

## 4. 输出说明
默认输出在后端运行目录下的任务输出目录（实际路径见日志中的 task id 对应目录）。

## 5. 质量优化建议
- 参考音频建议：单人、干净、无背景音乐、5-15 秒
- 文本过长可切段
- GPU 显存不足时可降低并发或改用 CPU 路径
