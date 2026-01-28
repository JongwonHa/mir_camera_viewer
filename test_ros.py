# test_ros.py - ROS 카메라 토픽 확인

import requests
import base64
import hashlib

MIR_IP = "10.67.152.126"
USERNAME = "distributor"
PASSWORD = "distributor"

# SHA256 인증
password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
auth_string = f"{USERNAME}:{password_hash}"
credentials = base64.b64encode(auth_string.encode()).decode("utf-8")

headers = {
    "Authorization": f"Basic {credentials}",
    "Accept-Language": "en_US"
}

print("=" * 60)
print("MiR ROS 관련 API 탐색")
print("=" * 60)

# ROS 관련 엔드포인트 탐색
endpoints = [
    "/api/v2.0.0/system/setup/cameras",
    "/api/v2.0.0/registers",
    "/api/v2.0.0/io_modules",
    "/api/v2.0.0/settings",
    "/api/v2.0.0/log",
    "/api/v2.0.0/software/logs",
    "/api/v2.0.0/wifi/connections",
]

for endpoint in endpoints:
    try:
        url = f"http://{MIR_IP}{endpoint}"
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"\n✅ {endpoint}")
            content = response.text[:800]
            print(content)
    except Exception as e:
        print(f"❌ {endpoint}: {e}")

# 카메라 전체 정보 가져오기
print("\n" + "=" * 60)
print("카메라 전체 정보:")
print("=" * 60)

response = requests.get(
    f"http://{MIR_IP}/api/v2.0.0/system/setup/cameras",
    headers=headers,
    timeout=5
)

if response.status_code == 200:
    import json
    data = response.json()
    print(json.dumps(data, indent=2))
