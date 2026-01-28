# test_camera.py

import requests
import base64
import json

MIR_IP = "10.67.152.126"
USERNAME = "admin"
PASSWORD = "admin"

credentials = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode("utf-8")
headers = {
    "Authorization": f"Basic {credentials}",
    "Accept-Language": "en_US"
}

# 카메라 설정 정보 가져오기
endpoints = [
    "/api/v2.0.0/system/setup/cameras",
    "/system/setup/cameras",
    "/api/v2.0.0/status",
]

print("=" * 60)
print("MiR 카메라 API 테스트")
print("=" * 60)

for endpoint in endpoints:
    try:
        url = f"http://{MIR_IP}{endpoint}"
        print(f"\n테스트: {endpoint}")
        response = requests.get(url, headers=headers, timeout=5)
        print(f"상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            print(f"Content-Type: {content_type}")
            
            if 'json' in content_type:
                data = response.json()
                print("응답 내용:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                print(f"응답 길이: {len(response.content)} bytes")
    except Exception as e:
        print(f"에러: {e}")

print("\n" + "=" * 60)

# 추가: 다른 포트에서 카메라 스트림 확인
print("\n카메라 스트림 포트 테스트...")
stream_urls = [
    f"http://{MIR_IP}:8080/stream",
    f"http://{MIR_IP}:8080/video",
    f"http://{MIR_IP}:8081/",
    f"http://{MIR_IP}:4242/",
    f"http://{MIR_IP}/stream",
]

for url in stream_urls:
    try:
        response = requests.get(url, timeout=3, stream=True)
        content_type = response.headers.get('Content-Type', '')
        print(f"✅ {url} - 상태: {response.status_code}, 타입: {content_type}")
    except:
        print(f"❌ {url} - 연결 실패")
