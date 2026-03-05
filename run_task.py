import sys
import time
import requests
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("用法: python run_task.py <视频文件路径>")
        return

    video_path = Path(sys.argv[1]).resolve()
    if not video_path.exists():
        print(f"❌ 找不到文件: {video_path}")
        return

    print(f"🔄 正在上传视频: {video_path.name}...")
    url = "http://127.0.0.1:8000/api/v1/tasks/upload?target_language=zh"
    
    try:
        with open(video_path, 'rb') as f:
            files = {'file': (video_path.name, f, 'video/mp4')}
            resp = requests.post(url, files=files)
            resp.raise_for_status()
            task_id = resp.json()['id']
    except requests.exceptions.ConnectionError:
        print("❌ 连接后端失败！请确认已在另一个终端运行了服务 (例如: cd backend && conda activate VoxFlow && python app.py)")
        return
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        if 'resp' in locals() and hasattr(resp, 'text'):
            print(f"服务器返回: {resp.text}")
        return

    print(f"✅ 任务已创建，开始处理，ID: {task_id}")
    print("⏳ 本过程可能需要几分钟，请耐心等待...\n")

    # 轮询进度
    last_msg = ""
    while True:
        time.sleep(6)  # 每6秒查询一次
        try:
            res = requests.get(f"http://127.0.0.1:8000/api/v1/tasks/{task_id}").json()
            status = res.get('status', 'unknown')
            progress = res.get('progress', 0)
            msg = res.get('message', '')
            
            # 只在状态有更新时才打印输出
            current_msg = f"[{status.upper()}] 进度: {progress}% - {msg}"
            if current_msg != last_msg:
                print(current_msg)
                last_msg = current_msg

            if status == 'completed':
                out_dir = Path(__file__).parent / "backend" / "storage" / "outputs" / task_id
                print(f"\n🎉 任务完成！")
                print(f"📁 结果已存放在: {out_dir.resolve()}")
                break
            elif status == 'failed':
                print(f"\n❌ 任务处理失败: {msg}")
                break
        except Exception as e:
            # 忽略网络抖动
            pass

if __name__ == "__main__":
    main()
