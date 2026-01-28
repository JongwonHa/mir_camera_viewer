# test_camera2.py

import requests
import base64
import hashlib

MIR_IP = "10.67.152.126"
USERNAME = "admin"
PASSWORD = "admin"

# MiR는 SHA256 해시 인증을 사용할 수 있음
password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
auth_string = f"{USERNAME}:{password_hash}"
credentials = base64.b64encode(auth_string.encode()).decode("utf-8")

headers_sha256 = {
    "Authorization": f"Basic {credentials}",
    "Accept-Language": "en_US"
}

# 일반 Basic Auth
credentials_basic = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode("utf-8")
headers_basic = {
    "Authorization": f"Basic {credentials_basic}",
    "Accept-Language": "en_US"
}

print("=" * 60)
print("MiR 카메라 스트림 찾기")
print("=" * 60)

# 1. /stream 내용 확인
print("\n[1] /stream 내용 확인:")
try:
    response = requests.get(f"http://{MIR_IP}/stream", timeout=5)
    print(f"상태: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print("HTML 내용 (처음 2000자):")
    print("-" * 40)
    print(response.text[:2000])
    print("-" * 40)
except Exception as e:
    print(f"에러: {e}")

# 2. 8080 포트 탐색
print("\n[2] 8080 포트 경로 탐색:")
paths_8080 = [
    "/", "/video", "/stream", "/mjpg", "/mjpeg",
    "/video.mjpg", "/video.mjpeg", "/cam", "/camera",
    "/snapshot", "/image", "/image.jpg", "/snap.jpg",
    "/?action=stream", "/?action=snapshot"
]

for path in paths_8080:
    try:
        url = f"http://{MIR_IP}:8080{path}"
        response = requests.get(url, timeout=2, stream=True)
        content_type = response.headers.get('Content-Type', '')
        if response.status_code == 200:
            print(f"✅ {path} - 타입: {content_type}")
        else:
            print(f"❌ {path} - {response.status_code}")
    except:
        pass

# 3. SHA256 인증으로 카메라 API 시도
print("\n[3] SHA256 인증으로 카메라 API:")
try:
    response = requests.get(
        f"http://{MIR_IP}/api/v2.0.0/system/setup/cameras",
        headers=headers_sha256,
        timeout=5
    )
    print(f"상태: {response.status_code}")
    if response.status_code == 200:
        print(f"응답: {response.text[:500]}")
except Exception as e:
    print(f"에러: {e}")

# 4. 기본 포트 80에서 이미지 경로 탐색
print("\n[4] 포트 80 이미지 경로 탐색:")
paths_80 = [
    "/camera", "/camera.jpg", "/snapshot", "/snapshot.jpg",
    "/image", "/image.jpg", "/video", "/mjpeg",
    "/api/v2.0.0/cameras/image", "/api/v2.0.0/vision/image",
    "/v2.0.0/cameras", "/cameras"
]

for path in paths_80:
    try:
        url = f"http://{MIR_IP}{path}"
        response = requests.get(url, headers=headers_basic, timeout=2)
        content_type = response.headers.get('Content-Type', '')
        size = len(response.content)
        if response.status_code == 200:
            print(f"✅ {path} - 타입: {content_type}, 크기: {size} bytes")
    except:
        pass

print("\n" + "=" * 60)
