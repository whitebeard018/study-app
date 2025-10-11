import cv2
import numpy as np
from flask import Flask
from flask_socketio import SocketIO, emit
import base64
import time
import os

# ---- SETUP ----
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Cascade Load (check path!) ---
CASCADE_PATH = os.path.dirname(__file__)
face_cascade = cv2.CascadeClassifier(os.path.join(CASCADE_PATH, 'haarcascade_frontalface_default.xml'))
eye_cascade = cv2.CascadeClassifier(os.path.join(CASCADE_PATH, 'haarcascade_eye.xml'))
if face_cascade.empty() or eye_cascade.empty():
    raise Exception("Could not load Haar cascades. Check XML files and paths.")

# --- Timing variables (per user, for scale-up use session ids) ---
last_seen_time = time.time()
last_open_eyes_time = time.time()
FOCUS_THRESHOLD = 6    # seconds before "distracted"
EYES_CLOSED_THRESHOLD = 2 # seconds before "WAKE UP"

@app.route('/')
def index():
    return "Focus Detection Backend Running"

@socketio.on('connect')
def handle_connect():
    print(f'Client connected at {time.strftime("%X")}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected at {time.strftime("%X")}')

@socketio.on('frame')
def handle_frame(dataURL):
    global last_seen_time, last_open_eyes_time
    try:
        header, encoded = dataURL.split(",", 1)
        img_bytes = base64.b64decode(encoded)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, 1)
        if frame is None:
            emit('status', {'msg': "Frame decode error"})
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 5)

        eyes_detected = False
        face_detected = len(faces) > 0

        now = time.time()
        if not face_detected:
            if now - last_seen_time > FOCUS_THRESHOLD:
                emit('status', {'msg': "⚠️ You seem distracted!"})
                return
        else:
            last_seen_time = now
            for (x, y, w, h) in faces:
                roi_gray = gray[y:y + h, x:x + w]
                eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 3, 0, (24, 24))
                if len(eyes) > 0:
                    eyes_detected = True
                    last_open_eyes_time = now
                    break

            # If face but no eyes open
            if not eyes_detected and now - last_open_eyes_time > EYES_CLOSED_THRESHOLD:
                emit('status', {'msg': "🔔 WAKE UP! Eyes look closed."})
                return

        # If all is well
        emit('status', {'msg': "Focus OK"})

    except Exception as e:
        print("Error in handle_frame:", e)
        emit('status', {'msg': "Server error: "+str(e)})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000)
