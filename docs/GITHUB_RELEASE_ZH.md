# GitHub 发布步骤

## 1. 初始化仓库
```powershell
cd D:\Vows
git init
git add .
git commit -m "Initial open-source release"
```

## 2. 在 GitHub 创建空仓库
- 仓库名建议：`Vows`
- 不要勾选 `Add README`（本地已有）

## 3. 绑定远程并推送
```powershell
git remote add origin https://github.com/<your-name>/Vows.git
git branch -M main
git push -u origin main
```

## 4. 发布前二次检查
```powershell
git status
git ls-files | Select-String "\.env|checkpoints|hf_cache|storage/outputs|storage/uploads"
```
应无命中或仅命中文档说明项。

## 5. 建议仓库设置
- 打开 Issues
- 打开 Discussions
- 添加 Topics：`video-dubbing`, `tts`, `asr`, `translation`, `fastapi`
- 在 About 中补充简短说明

## 6. 建议首个 Release 内容
- 版本：`v0.1.0`
- 说明：支持本地视频自动配音 + 可选硬字幕
- 已知限制：需自行准备 IndexTTS 与模型权重
