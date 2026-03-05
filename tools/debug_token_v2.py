import os
import requests

# Manually load env
def load_env_manual(path):
    d = {}
    try:
        print(f"DEBUG: Reading from {path}")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"DEBUG: First 50 chars: {repr(content[:50])}")
            f.seek(0)
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    d[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error reading {path}: {e}")
    return d

env_vars = load_env_manual(r"D:\vid\VoxFlow\backend\.env")
token = env_vars.get("HF_TOKEN")

print(f"Loaded Token: {repr(token)}") # Use repr to see hidden chars like \n, \r or spaces

if not token:
    print("FATAL: Token is empty")
    exit()

headers = {"Authorization": f"Bearer {token}"}

print("\n--- Test 1: Official API (huggingface.co) ---")
try:
    response = requests.get("https://huggingface.co/api/whoami", headers=headers, timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Official API Error: {e}")

print("\n--- Test 2: Mirror API (hf-mirror.com) ---")
try:
    response = requests.get("https://hf-mirror.com/api/whoami", headers=headers, timeout=5)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"User: {response.json().get('name', 'Unknown')}")
    else:
        print(f"Body: {response.text}")
except Exception as e:
    print(f"Mirror API Error: {e}")
