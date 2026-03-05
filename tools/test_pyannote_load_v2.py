"""
测试加载 pyannote 模型 (带 PyTorch 2.6 兼容性修复)
"""
import os
import torch

# PyTorch 2.6 兼容性修复
# 添加安全全局类，允许加载 TorchVersion
try:
    torch.serialization.add_safe_globals([torch.torch_version.TorchVersion])
except Exception as e:
    print(f"Warning: Could not add safe globals: {e}")

# 另一种修复方式：Monkey patch torch.load
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    # 强制设置 weights_only=False 以兼容旧模型格式
    kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

hf_token = os.getenv("HF_TOKEN", "").strip()
if not hf_token:
    raise RuntimeError("HF_TOKEN is required. Set it in environment before running.")

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

print("Step 1: 验证 Token...")
from huggingface_hub import HfApi
api = HfApi(token=hf_token)
user_info = api.whoami()
print(f"✅ Token 有效! 用户: {user_info['name']}")

print("\nStep 2: 尝试加载 pyannote 模型...")
try:
    from pyannote.audio import Pipeline
    pipeline = Pipeline.from_pretrained(
        'pyannote/speaker-diarization-3.1',
        use_auth_token=hf_token
    )
    print("✅ SUCCESS! Pipeline 加载成功!")
    print(f"Pipeline 类型: {type(pipeline)}")
except Exception as e:
    print(f"❌ 加载失败: {e}")
    import traceback
    traceback.print_exc()
