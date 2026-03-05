import os
import requests
from dotenv import load_dotenv

load_dotenv(r"D:\vid\VoxFlow\backend\.env")
token = os.getenv("HF_TOKEN")

print(f"Testing token: {token}")

headers = {"Authorization": f"Bearer {token}"}
response = requests.get("https://huggingface.co/api/whoami", headers=headers)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")
