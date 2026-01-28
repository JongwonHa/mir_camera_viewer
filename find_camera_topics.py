# find_camera_topics.py - ROS 카메라 토픽 찾기 (인증 포함)

import websocket
import json
import base64
import hashlib

MIR_IP = "10.67.152.126"
USERNAME = "admin"
PASSWORD = "admin"

# SHA256 인증 헤더 생성
password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
auth_string = f"{USERNAME}:{password_hash}"
credentials = base64.b64encode(auth_string.encode()).decode("utf-8")

ws_url = f"ws://{MIR_IP}:9090"

print("=" * 60)
print("ROS Bridge로 카메라 토픽 찾기 (인증 포함)")
print("=" * 60)

try:
    # 인증 헤더 추가
    headers = {
        "Authorization": f"Basic {credentials}"
    }
    
    ws = websocket.create_connection(
        ws_url, 
        timeout=10,
        header=headers
    )
    print(f"✅ 연결 성공: {ws_url}\n")
    
    # 모든 토픽 리스트 요청
    request = json.dumps({
        "op": "call_service",
        "service": "/rosapi/topics"
    })
    ws.send(request)
    
    result = ws.recv()
    data = json.loads(result)
    
    if "values" in data and "topics" in data["values"]:
        topics = data["values"]["topics"]
        
        print("📷 카메라 관련 토픽:")
        print("-" * 40)
        camera_topics = []
        for topic in topics:
            if any(keyword in topic.lower() for keyword in ["camera", "image", "rgb", "depth", "color"]):
                print(f"  {topic}")
                camera_topics.append(topic)
        
        print(f"\n📋 전체 토픽 수: {len(topics)}")
        
        print("\n🎯 이미지 토픽 (compressed):")
        for topic in camera_topics:
            if "compressed" in topic:
                print(f"  ⭐ {topic}")
                
        print("\n🎯 이미지 토픽 (raw):")
        for topic in camera_topics:
            if "image_raw" in topic and "compressed" not in topic:
                print(f"  ⭐ {topic}")
    else:
        print("응답:", json.dumps(data, indent=2))
    
    ws.close()
    
except Exception as e:
    print(f"❌ 에러: {e}")
    print("\n다른 인증 방식 시도 중...")
    
    # 일반 Basic Auth로 재시도
    try:
        auth_basic = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode("utf-8")
        headers2 = {"Authorization": f"Basic {auth_basic}"}
        
        ws = websocket.create_connection(ws_url, timeout=10, header=headers2)
        print(f"✅ 일반 인증으로 연결 성공!")
        ws.close()
    except Exception as e2:
        print(f"❌ 일반 인증도 실패: {e2}")

print("\n" + "=" * 60)
