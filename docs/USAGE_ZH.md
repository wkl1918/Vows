# 使用说明

🛠️ Vows Usage Guide

Languages: [简体中文](USAGE_ZH.md) · [English](USAGE_EN.md) · [日本語](USAGE_JA.md)

## 1. 一键脚本（Windows）
- `一键处理视频.bat`：处理视频并生成配音（不硬烧字幕）
- `一键处理视频并加硬字幕.bat`：处理视频并写入硬字幕

使用方式：将视频文件拖拽到对应 bat 文件上。

可选目标语言：
- 默认语言是 `zh`
- 拖拽后若未传第二参数，脚本会弹出 50 语言代码提示供选择
- 也可以在命令行中指定第二个参数作为目标语言，例如：
```powershell
一键处理视频.bat "D:/path/to/input.mp4" en
一键处理视频并加硬字幕.bat "D:/path/to/input.mp4" ja
```

前端语言选择：
- 前端上传页已提供 50 种目标语言下拉框，上传前可直接选择。

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
python run_task.py "D:/path/to/input.mp4" zh
```
或
```powershell
python run_task_with_subtitles.py "D:/path/to/input.mp4" zh
```

参数说明：
- 第一个参数：输入视频路径
- 第二个参数（可选）：目标语言代码，默认 `zh`

常见目标语言示例：
- `zh`：中文
- `en`：英文
- `ja`：日文
- `ko`：韩文
- `es`：西班牙语
- `fr`：法语
- `de`：德语
- `ru`：俄语
- `it`：意大利语
- `pt`：葡萄牙语
- `ar`：阿拉伯语
- `hi`：印地语
- `th`：泰语
- `vi`：越南语
- `tr`：土耳其语
- `nl`：荷兰语
- `pl`：波兰语
- `id`：印尼语
- `ms`：马来语
- `fa`：波斯语
- `uk`：乌克兰语
- `cs`：捷克语
- `sk`：斯洛伐克语
- `hu`：匈牙利语
- `ro`：罗马尼亚语
- `bg`：保加利亚语
- `hr`：克罗地亚语
- `sl`：斯洛文尼亚语
- `sr`：塞尔维亚语
- `da`：丹麦语
- `sv`：瑞典语
- `no`：挪威语
- `fi`：芬兰语
- `et`：爱沙尼亚语
- `lv`：拉脱维亚语
- `lt`：立陶宛语
- `el`：希腊语
- `he`：希伯来语
- `bn`：孟加拉语
- `ta`：泰米尔语
- `te`：泰卢固语
- `mr`：马拉地语
- `gu`：古吉拉特语
- `kn`：卡纳达语
- `ml`：马拉雅拉姆语
- `ur`：乌尔都语
- `sw`：斯瓦希里语
- `af`：南非语
- `fil`：菲律宾语
- `ca`：加泰罗尼亚语

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
