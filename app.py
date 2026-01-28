# app.py - MiR250 카메라 뷰어 (RAW 이미지 지원)

from flask import Flask, render_template, Response, jsonify
import websocket
import json
import base64
import hashlib
import threading
import time
import numpy as np
from io import BytesIO

# PIL 설치 필요: pip install Pillow
from PIL import Image

app = Flask(__name__)

# ============ 설정 ============
MIR_IP = "10.67.152.126"
USERNAME = "distributor"
PASSWORD = "distributor"
# ==============================

# SHA256 인증
password_hash = hashlib.sha256(PASSWORD.encode()).hexdigest()
auth_string = f"{USERNAME}:{password_hash}"
credentials = base64.b64encode(auth_string.encode()).decode("utf-8")

# 이미지 저장
latest_images = {
    "left_infra": None,
    "right_infra": None,
}

status_info = {
    "ws_connected": False,
    "last_message_time": None,
    "message_count": 0,
    "errors": [],
}


def raw_to_jpeg(data_base64, width, height, encoding):
    """ROS raw 이미지를 JPEG로 변환"""
    try:
        # Base64 디코딩
        raw_bytes = base64.b64decode(data_base64)
        
        # numpy array로 변환
        if encoding == "8UC1" or encoding == "mono8":
            # 흑백 이미지
            img_array = np.frombuffer(raw_bytes, dtype=np.uint8)
            img_array = img_array.reshape((height, width))
            img = Image.fromarray(img_array, mode='L')
        elif encoding == "16UC1" or encoding == "mono16":
            # 16비트 깊이 이미지 -> 8비트로 정규화
            img_array = np.frombuffer(raw_bytes, dtype=np.uint16)
            img_array = img_array.reshape((height, width))
            # 정규화 (0-65535 -> 0-255)
            img_array = (img_array / 256).astype(np.uint8)
            img = Image.fromarray(img_array, mode='L')
        elif encoding == "rgb8":
            img_array = np.frombuffer(raw_bytes, dtype=np.uint8)
            img_array = img_array.reshape((height, width, 3))
            img = Image.fromarray(img_array, mode='RGB')
        elif encoding == "bgr8":
            img_array = np.frombuffer(raw_bytes, dtype=np.uint8)
            img_array = img_array.reshape((height, width, 3))
            img_array = img_array[:, :, ::-1]  # BGR -> RGB
            img = Image.fromarray(img_array, mode='RGB')
        else:
            # 기본: 흑백으로 시도
            img_array = np.frombuffer(raw_bytes, dtype=np.uint8)
            img_array = img_array.reshape((height, width))
            img = Image.fromarray(img_array, mode='L')
        
        # ⭐ 반시계 방향 90도 회전 추가!
        img = img.rotate(90, expand=True)
        
        # JPEG로 인코딩
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=80)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"이미지 변환 에러: {e}")
        return None


def on_message(ws, message):
    """ROS 메시지 수신"""
    global latest_images, status_info
    try:
        data = json.loads(message)
        status_info["message_count"] += 1
        status_info["last_message_time"] = time.strftime("%H:%M:%S")
        
        if "topic" not in data or "msg" not in data:
            return
            
        topic = data["topic"]
        msg = data["msg"]
        
        # RAW 이미지 처리 (sensor_msgs/Image)
        if "height" in msg and "width" in msg and "data" in msg:
            height = msg["height"]
            width = msg["width"]
            encoding = msg.get("encoding", "8UC1")
            img_data = msg["data"]
            
            # JPEG로 변환
            jpeg_bytes = raw_to_jpeg(img_data, width, height, encoding)
            
            if jpeg_bytes:
                # 토픽별 저장
                if "floor_left" in topic and "infra1" in topic:
                    latest_images["left_infra"] = jpeg_bytes
                    print(f"✅ 왼쪽 적외선: {width}x{height} ({len(jpeg_bytes)} bytes)")
                elif "floor_right" in topic and "infra1" in topic:
                    latest_images["right_infra"] = jpeg_bytes
                    print(f"✅ 오른쪽 적외선: {width}x{height} ({len(jpeg_bytes)} bytes)")
                elif "floor_left" in topic and "depth" in topic:
                    latest_images["left_depth"] = jpeg_bytes
                    print(f"✅ 왼쪽 깊이: {width}x{height} ({len(jpeg_bytes)} bytes)")
                elif "floor_right" in topic and "depth" in topic:
                    latest_images["right_depth"] = jpeg_bytes
                    print(f"✅ 오른쪽 깊이: {width}x{height} ({len(jpeg_bytes)} bytes)")
                    
    except Exception as e:
        error_msg = f"메시지 처리 에러: {e}"
        print(error_msg)
        status_info["errors"].append(error_msg)
        if len(status_info["errors"]) > 10:
            status_info["errors"] = status_info["errors"][-10:]


def on_error(ws, error):
    print(f"❌ WebSocket 에러: {error}")


def on_close(ws, code, msg):
    status_info["ws_connected"] = False
    print("🔌 연결 종료")


def on_open(ws):
    status_info["ws_connected"] = True
    print("✅ WebSocket 연결 성공!")
    
    # RAW 이미지 토픽 구독 (compressed 대신!)
    topics = [
        "/camera_floor_left/driver/infra1/image_rect_raw",
        "/camera_floor_right/driver/infra1/image_rect_raw",
    ]
    
    for topic in topics:
        subscribe_msg = json.dumps({
            "op": "subscribe",
            "topic": topic,
            "type": "sensor_msgs/Image",
            "throttle_rate": 100,  # 10FPS
            "queue_length": 1
        })
        ws.send(subscribe_msg)
        print(f"📡 구독: {topic}")


def start_websocket():
    ws_url = f"ws://{MIR_IP}:9090"
    headers = {"Authorization": f"Basic {credentials}"}
    
    while True:
        try:
            print(f"\n🔄 연결 시도: {ws_url}")
            ws = websocket.WebSocketApp(
                ws_url,
                header=headers,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever(ping_interval=30)
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
        
        print("⏳ 5초 후 재연결...")
        time.sleep(5)


def generate_stream(camera_key):
    """MJPEG 스트림"""
    while True:
        jpeg_bytes = latest_images.get(camera_key)
        if jpeg_bytes:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_bytes + b'\r\n')
        time.sleep(0.5)


@app.route('/')
def index():
    return render_template('index.html', robot_ip=MIR_IP)


@app.route('/stream/<camera>')
def stream(camera):
    valid = ["left_infra", "right_infra", "left_depth", "right_depth"]
    if camera in valid:
        return Response(generate_stream(camera),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    return "Not found", 404


@app.route('/snapshot/<camera>')
def snapshot(camera):
    valid = ["left_infra", "right_infra", "left_depth", "right_depth"]
    if camera in valid:
        jpeg_bytes = latest_images.get(camera)
        if jpeg_bytes:
            return Response(jpeg_bytes, mimetype='image/jpeg')
        return "No image", 404
    return "Not found", 404


@app.route('/status')
def status():
    return jsonify({
        "connected": status_info["ws_connected"],
        "message_count": status_info["message_count"],
        "last_message": status_info["last_message_time"],
        "images": {k: v is not None for k, v in latest_images.items()},
        "errors": status_info["errors"][-3:]
    })


@app.route('/debug')
def debug():
    imgs = latest_images
    return f"""
    <html>
    <head>
        <title>디버그</title>
        <meta http-equiv="refresh" content="2">
        <style>
            body {{ font-family: monospace; background: #1a1a2e; color: #0f0; padding: 20px; }}
            .ok {{ color: #0f0; }}
            .err {{ color: #f00; }}
        </style>
    </head>
    <body>
        <h1>🔧 MiR 카메라 디버그</h1>
        <pre>
WebSocket: {'✅ 연결됨' if status_info['ws_connected'] else '❌ 끊김'}
메시지 수: {status_info['message_count']}
마지막: {status_info['last_message_time'] or 'N/A'}

이미지 상태:
  왼쪽 적외선: {'✅ ' + str(len(imgs['left_infra'])) + ' bytes' if imgs['left_infra'] else '❌ 없음'}
  오른쪽 적외선: {'✅ ' + str(len(imgs['right_infra'])) + ' bytes' if imgs['right_infra'] else '❌ 없음'}
  왼쪽 깊이: {'✅ ' + str(len(imgs['left_depth'])) + ' bytes' if imgs['left_depth'] else '❌ 없음'}
  오른쪽 깊이: {'✅ ' + str(len(imgs['right_depth'])) + ' bytes' if imgs['right_depth'] else '❌ 없음'}
        </pre>
        <p>2초마다 새로고침</p>
    </body>
    </html>
    """


if __name__ == '__main__':
    ws_thread = threading.Thread(target=start_websocket, daemon=True)
    ws_thread.start()
    
    print("=" * 50)
    print("🤖 MiR250 카메라 뷰어")
    print(f"📡 로봇: {MIR_IP}")
    print("🌐 http://localhost:5001")
    print("🔧 http://localhost:5001/debug")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)
