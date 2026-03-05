
import asyncio
import edge_tts

TEXT = "你好，这是一个测试。"
VOICE = "zh-CN-XiaoxiaoNeural"
OUTPUT = "test.mp3"

async def main():
    print(f"Testing TTS with voice: {VOICE}")
    communicate = edge_tts.Communicate(TEXT, VOICE)
    try:
        await communicate.save(OUTPUT)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
