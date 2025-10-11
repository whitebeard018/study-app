# backend/app.py
import base64
import io
import os
import time
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
from PIL import Image

app = Flask(__name__, static_folder='../frontend', static_url_path='/')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@socketio.on('connect')
def on_connect():
    print('Client connected', time.strftime('%X'))

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected', time.strftime('%X'))

# Save directory for debug frames
SAVE_DIR = os.path.join(os.path.dirname(__file__), 'received_frames')
os.makedirs(SAVE_DIR, exist_ok=True)

@socketio.on('frame')
def handle_frame(data):
    """
    data: dataURL string like "data:image/jpeg;base64,/9j/..."
    Decodes and saves every 5th frame to disk (debug). Emits a quick status back.
    """
    try:
        # strip header if present
        header, b64 = (data.split(',',1) + [None])[:2]
        img_bytes = base64.b64decode(b64)
        img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
        timestamp = int(time.time()*1000)

        if not hasattr(handle_frame, 'counter'):
            handle_frame.counter = 0
        handle_frame.counter += 1

        saved = False
        # save periodically to avoid heavy disk writes
        if handle_frame.counter % 5 == 0:
            filename = os.path.join(SAVE_DIR, f'frame_{timestamp}.jpg')
            img.save(filename, 'JPEG', quality=75)
            print('Saved frame to', filename)
            saved = True

        # Respond immediately
        emit('status', {'distracted': False, 'msg': 'frame received', 'saved': saved})
    except Exception as e:
        print('Error decoding frame:', e)
        emit('status', {'distracted': False, 'msg': 'error', 'error': str(e)})

@socketio.on('detection')
def handle_detection(data):
    """
    Optional: client-side detection events (if you want to persist)
    Example data: {"type":"eyes_closed","duration":2.5,"ts":1234567890}
    """
    print('Detection event:', data)
    # TODO: save detection events to DB or file
    emit('ack', {'ok': True})

if __name__ == '__main__':
    # Use the venv's python to run: .\venv\Scripts\python.exe app.py
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

