"""
深度诊断 Token 问题
排查：字符编码、隐藏字符、Token格式、请求头格式等
"""
import os
import requests

# 手动读取 .env
def load_env_manual(path):
    d = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
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

env_path = r"D:\vid\VoxFlow\backend\.env"
env_vars = load_env_manual(env_path)
token = env_vars.get("HF_TOKEN")

print("=" * 60)
print("【1】Token 基础信息")
print("=" * 60)
print(f"Token 值: {token}")
print(f"Token 长度: {len(token) if token else 0}")
print(f"Token repr: {repr(token)}")

if token:
    # 检查隐藏字符
    print(f"\n【2】Token 字符分析")
    print("-" * 40)
    has_issue = False
    for i, char in enumerate(token):
        if not char.isalnum() and char != '_':
            print(f"  ⚠️  位置 {i}: 发现非常规字符 '{char}' (ASCII: {ord(char)})")
            has_issue = True
    if not has_issue:
        print("  ✅ 所有字符正常 (字母、数字、下划线)")
    
    # 检查前缀
    print(f"\n【3】Token 格式检查")
    print("-" * 40)
    if token.startswith("hf_"):
        print("  ✅ Token 以 'hf_' 开头 (格式正确)")
    else:
        print(f"  ⚠️  Token 不以 'hf_' 开头: '{token[:10]}...'")
    
    # 测试不同的请求方式
    print(f"\n【4】API 连接测试")
    print("-" * 40)
    
    # 方式1: 标准 Bearer
    print("\n  测试 A: 标准 Bearer 格式")
    headers_a = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get("https://hf-mirror.com/api/whoami", headers=headers_a, timeout=10)
        print(f"    状态码: {resp.status_code}")
        print(f"    响应: {resp.text[:200]}")
    except Exception as e:
        print(f"    错误: {e}")
    
    # 方式2: 无 Bearer 前缀 (少数 API 使用)
    print("\n  测试 B: 直接使用 Token (无 Bearer)")
    headers_b = {"Authorization": token}
    try:
        resp = requests.get("https://hf-mirror.com/api/whoami", headers=headers_b, timeout=10)
        print(f"    状态码: {resp.status_code}")
        print(f"    响应: {resp.text[:200]}")
    except Exception as e:
        print(f"    错误: {e}")
    
    # 方式3: 检查是否是网络/SSL问题
    print("\n  测试 C: 检查网络连通性 (访问公开 API)")
    try:
        resp = requests.get("https://hf-mirror.com/api/models?limit=1", timeout=10)
        print(f"    状态码: {resp.status_code}")
        if resp.status_code == 200:
            print("    ✅ 网络连接正常，能访问 HF Mirror")
        else:
            print(f"    ⚠️  响应异常: {resp.text[:100]}")
    except Exception as e:
        print(f"    ❌ 网络错误: {e}")

    # 方式4: 检查 SSL 证书时间
    print(f"\n【5】SSL/TLS 连接诊断")
    print("-" * 40)
    try:
        import ssl
        import socket
        from datetime import datetime
        
        hostname = "hf-mirror.com"
        context = ssl.create_default_context()
        
        with socket.create_connection((hostname, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                not_before = cert.get('notBefore')
                not_after = cert.get('notAfter')
                print(f"  证书有效期起始: {not_before}")
                print(f"  证书有效期结束: {not_after}")
                print(f"  当前系统时间: {datetime.now()}")
                
                # 解析证书时间
                from datetime import datetime
                import time
                cert_start = ssl.cert_time_to_seconds(not_before)
                cert_end = ssl.cert_time_to_seconds(not_after)
                now = time.time()
                
                if now < cert_start:
                    print(f"  ⚠️  警告: 系统时间早于证书生效时间!")
                elif now > cert_end:
                    print(f"  ⚠️  警告: 系统时间晚于证书过期时间!")
                else:
                    print(f"  ✅ 系统时间在证书有效期内")
                    
    except Exception as e:
        print(f"  SSL 诊断失败: {e}")

    print(f"\n【6】环境变量检查")
    print("-" * 40)
    hf_endpoint = os.environ.get("HF_ENDPOINT", "(未设置)")
    http_proxy = os.environ.get("HTTP_PROXY", "(未设置)")
    https_proxy = os.environ.get("HTTPS_PROXY", "(未设置)")
    print(f"  HF_ENDPOINT: {hf_endpoint}")
    print(f"  HTTP_PROXY: {http_proxy}")
    print(f"  HTTPS_PROXY: {https_proxy}")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
