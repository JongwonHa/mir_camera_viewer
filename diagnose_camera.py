# diagnose_camera.py - 카메라 토픽 상세 진단

import websocket
import json
import base64
import hashlib
import time
import threading

MIR_IP = "10.67.152.126"
USERNAME = "admin"
PASSWORD = "admin"

# SHA256 인증
password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
auth_string = f"{USERNAME}:{password_hash}"
credentials = base64.b64encode(auth_string.encode()).decode("utf-8")

ws_url = f"ws://{MIR_IP}:9090"
headers = {"Authorization": f"Basic {credentials}"}

received_messages = []
topic_types = {}

def on_message(ws, message):
    global received_messages
    try:
        data = json.loads(message)
        received_messages.append(data)
        
        # 서비스 응답 처리
        if data.get("op") == "service_response":
            if "values" in data:
                print(f"\n📋 서비스 응답 수신")
            return
        
        # 토픽 메시지
        if "topic" in data:
            topic = data.get("topic", "unknown")
            msg = data.get("msg", {})
            print(f"\n📨 토픽 메시지: {topic}")
            print(f"   메시지 키: {list(msg.keys()) if isinstance(msg, dict) else type(msg)}")
            
            if "data" in msg:
                data_len = len(msg["data"]) if msg["data"] else 0
                print(f"   data 길이: {data_len} bytes")
            if "format" in msg:
                print(f"   format: {msg['format']}")
                
    except Exception as e:
        print(f"❌ 메시지 파싱 에러: {e}")


def on_error(ws, error):
    print(f"❌ 에러: {error}")


def on_close(ws, code, msg):
    print(f"🔌 연결 종료: {code}")


def on_open(ws):
    print("✅ WebSocket 연결 성공!\n")
    
    # 1. 토픽 타입 조회
    print("=" * 50)
    print("1️⃣ 카메라 토픽 타입 조회")
    print("=" * 50)
    
    camera_topics = [
        "/camera_floor_left/driver/infra1/image_rect_raw",
        "/camera_floor_left/driver/infra1/image_rect_raw/compressed",
        "/camera_floor_right/driver/infra1/image_rect_raw",
        "/camera_floor_right/driver/infra1/image_rect_raw/compressed",
        "/camera_floor_left/driver/depth/image_rect_raw",
        "/camera_floor_left/driver/depth/image_rect_raw/compressed",
    ]
    
    for topic in camera_topics:
        req = json.dumps({
            "op": "call_service",
            "service": "/rosapi/topic_type",
            "args": {"topic": topic}
        })
        ws.send(req)
        time.sleep(0.2)
    
    time.sleep(1)
    
    # 2. 발행자 수 확인
    print("\n" + "=" * 50)
    print("2️⃣ 토픽 발행자 수 확인")
    print("=" * 50)
    
    for topic in camera_topics:
        req = json.dumps({
            "op": "call_service", 
            "service": "/rosapi/publishers",
            "args": {"topic": topic}
        })
        ws.send(req)
        time.sleep(0.2)
    
    time.sleep(1)
    
    # 3. 구독 테스트
    print("\n" + "=" * 50)
    print("3️⃣ 토픽 구독 테스트 (10초 대기)")
    print("=" * 50)
    
    test_topics = [
        # compressed 버전
        ("/camera_floor_left/driver/infra1/image_rect_raw/compressed", "sensor_msgs/CompressedImage"),
        # raw 버전
        ("/camera_floor_left/driver/infra1/image_rect_raw", "sensor_msgs/Image"),
        # depth compressed
        ("/camera_floor_left/driver/depth/image_rect_raw/compressed", "sensor_msgs/CompressedImage"),
    ]
    
    for topic, msg_type in test_topics:
        print(f"\n📡 구독 시도: {topic}")
        print(f"   타입: {msg_type}")
        
        subscribe_msg = json.dumps({
            "op": "subscribe",
            "topic": topic,
            "type": msg_type,
            "throttle_rate": 1000,  # 1초에 1번
            "queue_length": 1
        })
        ws.send(subscribe_msg)
        time.sleep(0.3)
    
    print("\n⏳ 10초 동안 메시지 대기 중...")


print("=" * 60)
print("MiR250 카메라 토픽 진단")
print("=" * 60)

try:
    ws = websocket.WebSocketApp(
        ws_url,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # 15초 후 자동 종료
    def close_after_timeout():
        time.sleep(15)
        print("\n\n⏰ 시간 초과 - 연결 종료")
        ws.close()
    
    timer = threading.Thread(target=close_after_timeout, daemon=True)
    timer.start()
    
    ws.run_forever()
    
except Exception as e:
    print(f"❌ 연결 실패: {e}")

# 결과 요약
print("\n" + "=" * 60)
print("📊 진단 결과 요약")
print("=" * 60)
print(f"총 수신 메시지: {len(received_messages)}개")

# 서비스 응답 분석
service_responses = [m for m in received_messages if m.get("op") == "service_response"]
print(f"서비스 응답: {len(service_responses)}개")

for resp in service_responses:
    if "values" in resp:
        print(f"  → {resp['values']}")

# 토픽 메시지 분석  
topic_messages = [m for m in received_messages if "topic" in m]
print(f"토픽 메시지: {len(topic_messages)}개")

if topic_messages:
    print("✅ 카메라 이미지 수신 성공!")
else:
    print("❌ 카메라 이미지 수신 실패")
    print("\n💡 가능한 원인:")
    print("   1. 카메라가 비활성화 상태")
    print("   2. 로봇이 특정 모드에서만 카메라 발행")
    print("   3. 토픽 이름이나 메시지 타입이 다름")

print("=" * 60)
