import sys
import time
import requests
import subprocess
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("用法: python run_task_with_subtitles.py <视频文件路径> [目标语言代码]")
        print("示例: python run_task_with_subtitles.py \"D:/demo.mp4\" zh")
        return

    video_path = Path(sys.argv[1]).resolve()
    if not video_path.exists():
        print(f"❌ 找不到文件: {video_path}")
        return

    target_language = (sys.argv[2] if len(sys.argv) >= 3 else "zh").strip() or "zh"
    print(f"🔄 正在上传视频: {video_path.name} (目标语言: {target_language})...")
    url = f"http://127.0.0.1:8000/api/v1/tasks/upload?target_language={target_language}"
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': (video_path.name, f, 'video/mp4')}
            resp = requests.post(url, files=files)
            resp.raise_for_status()
            task_id = resp.json()['id']
    except requests.exceptions.ConnectionError:
        print("❌ 连接后端失败！请确认后端服务已运行。")
        return
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        return

    print(f"✅ 任务已创建，开始处理，ID: {task_id}")
    print("⏳ 等待服务端完成核心处理流程 (提音/配音/合并)...\n")

    # 轮询后端进度
    last_msg = ""
    while True:
        time.sleep(6)
        try:
            res = requests.get(f"http://127.0.0.1:8000/api/v1/tasks/{task_id}").json()
            status = res.get('status', 'unknown')
            progress = res.get('progress', 0)
            msg = res.get('message', '')
            
            current_msg = f"[{status.upper()}] 进度: {progress}% - {msg}"
            if current_msg != last_msg:
                print(current_msg)
                last_msg = current_msg

            if status == 'completed':
                break
            elif status == 'failed':
                print(f"\n❌ 后端处理失败: {msg}")
                return
        except Exception:
            pass

    out_dir = Path(__file__).parent / "backend" / "storage" / "outputs" / task_id
    final_video : Path = out_dir / f"final_{video_path.name}"
    
    if not final_video.exists():
        print(f"\n❌ 后端显示完成，但没有找到输出文件: {final_video}")
        return

    srt_file = out_dir / f"final_{video_path.stem}.srt"
    subtitled_video = out_dir / f"final_{video_path.stem}_subtitled.mp4"

    # ========= 1. 使用离线模型生成字幕 (ASR) =========
    print("\n🎬 核心音视频合并已完成！开始加载本地离线 ASR 模型生成字幕...")
    try:
        from faster_whisper import WhisperModel
        model_dir = Path(__file__).parent / "backend" / "models" / "large-v3"
        model_source = str(model_dir) if model_dir.exists() else "large-v3"

        try:
            import torch
            use_cuda = torch.cuda.is_available()
        except Exception:
            use_cuda = False
        asr_device = "cuda" if use_cuda else "cpu"
        compute_type = "float16" if use_cuda else "int8"
        
        print(">> 正在加载 ASR 模型 (首次运行可能下载, 需要一点时间)...")
        model = WhisperModel(model_source, device=asr_device, compute_type=compute_type)
        
        print(f">> 正在听写最新的视频: {final_video.name}")
        # Subtitles follow dubbing target language to keep display and audio consistent.
        segments, info = model.transcribe(str(final_video), language=target_language, vad_filter=True, beam_size=5)

        def ts(t):
            h = int(t // 3600)
            m = int((t % 3600) // 60)
            s = int(t % 60)
            ms = int(round((t - int(t)) * 1000))
            if ms >= 1000: 
                s += 1
                ms -= 1000
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

        lines = []
        for i, s in enumerate(segments, 1):
            txt = (s.text or "").strip()
            if not txt: continue
            lines += [str(i), f"{ts(s.start)} --> {ts(s.end)}", txt, ""]
        
        srt_file.write_text("\n".join(lines), encoding="utf-8")
        print(f"✅ 字幕时间轴文件已生成: {srt_file.name}")
    except Exception as e:
        print(f"❌ 生成字幕失败: {e}")
        return

    # ========= 2. 使用 FFmpeg 烧录硬字幕 =========
    print("\n🔥 正在将硬字幕烧录到底部 (使用项目自带ffmpeg)...")
    ffmpeg_exe = Path(__file__).parent / "tools" / "ffmpeg" / "ffmpeg.exe"
    
    # 注意：我们使用 cwd=str(out_dir) 来运行，这样可以避免路径里反斜杠引起的 ffmpeg 解析错误
    cmd = [
        str(ffmpeg_exe), "-y", "-i", final_video.name,
        # 调用微软雅黑、设置居中样式（类似之前成功的用法）
        "-vf", f"subtitles={srt_file.name}:force_style='Alignment=2,MarginV=26,FontName=Microsoft YaHei,Fontsize=16,Outline=1,Shadow=0'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy",
        subtitled_video.name
    ]

    try:
        proc = subprocess.run(cmd, cwd=str(out_dir), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if proc.returncode == 0:
            print(f"\n🎉 完美收工！视频加字幕全流程已完成！")
            print(f"📁 【无字幕原始配音视频】: {final_video.resolve()}")
            print(f"📁 【最终成片(硬字幕)】: {subtitled_video.resolve()}")
        else:
            print(f"❌ 烧录字幕失败，返回码: {proc.returncode}")
            print(proc.stdout)
    except Exception as e:
         print(f"❌ ffmpeg 执行出错: {e}")

if __name__ == "__main__":
    main()
