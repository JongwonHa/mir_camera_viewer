# test_ros_bridge.py - ROS Bridge 및 비디오 포트 탐색

import requests
import socket
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
print("MiR 포트 스캔 및 ROS Bridge 확인")
print("=" * 60)

# 1. 주요 포트 스캔
ports_to_check = [
    (80, "HTTP Web UI"),
    (443, "HTTPS"),
    (8080, "HTTP Alt"),
    (8081, "Video Stream?"),
    (8082, "Video Stream?"),
    (9090, "ROS Bridge WebSocket"),
    (9091, "ROS Bridge Alt"),
    (11311, "ROS Master"),
    (1883, "MQTT"),
    (5000, "Flask?"),
    (554, "RTSP"),
    (8554, "RTSP Alt"),
    (8000, "HTTP Alt"),
    (3000, "Web App"),
    (4000, "Web App"),
]

print("\n[1] 포트 스캔:")
open_ports = []
for port, desc in ports_to_check:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((MIR_IP, port))
    if result == 0:
        print(f"✅ 포트 {port} 열림 - {desc}")
        open_ports.append(port)
    sock.close()

# 2. 열린 포트에서 HTTP 테스트
print("\n[2] 열린 포트 HTTP 테스트:")
for port in open_ports:
    try:
        url = f"http://{MIR_IP}:{port}/"
        response = requests.get(url, timeout=3, headers=headers)
        content_type = response.headers.get('Content-Type', '')
        print(f"포트 {port}: 상태={response.status_code}, 타입={content_type}")
        
        # 응답 내용 일부 출력
        if 'json' in content_type:
            print(f"  JSON: {response.text[:200]}")
        elif 'html' in content_type:
            print(f"  HTML 길이: {len(response.text)} bytes")
    except Exception as e:
        print(f"포트 {port}: {e}")

# 3. ROS Bridge WebSocket 테스트 (9090)
print("\n[3] ROS Bridge WebSocket 테스트 (포트 9090):")
try:
    import websocket
    ws_url = f"ws://{MIR_IP}:9090"
    ws = websocket.create_connection(ws_url, timeout=3)
    print(f"✅ WebSocket 연결 성공: {ws_url}")
    
    # 토픽 리스트 요청
    import json
    request = json.dumps({
        "op": "call_service",
        "service": "/rosapi/topics"
    })
    ws.send(request)
    result = ws.recv()
    print(f"응답: {result[:500]}")
    ws.close()
except ImportError:
    print("websocket-client 설치 필요: pip install websocket-client")
except Exception as e:
    print(f"❌ WebSocket 연결 실패: {e}")

# 4. RTSP 스트림 테스트
print("\n[4] RTSP 스트림 URL 테스트:")
rtsp_urls = [
    f"rtsp://{MIR_IP}:554/stream",
    f"rtsp://{MIR_IP}:554/camera",
    f"rtsp://{MIR_IP}:8554/stream",
]
for url in rtsp_urls:
    print(f"  테스트할 URL: {url}")

print("\n" + "=" * 60)
print("완료!")
print("=" * 60)
