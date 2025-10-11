import cv2
import os
import time
import winsound  # for sound on Windows
# (If on Mac/Linux, we can use 'playsound' or 'pygame' instead)

# ✅ Ensure we are in the correct folder
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ✅ Load Haar cascades
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')

# ✅ Start camera
cap = cv2.VideoCapture(0)

# Focus tracking
last_seen_time = time.time()
focus_threshold = 6  # seconds before alert triggers
alert_cooldown = 1    # seconds between beeps

last_alert_time = 0

print("🎥 Focus detector running. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        # No face detected
        if time.time() - last_seen_time > focus_threshold:
            cv2.putText(frame, "⚠️ You seem distracted!", (50, 80),
                        cv2.FONT_HERSHEY_DUPLEX, 1, (0, 0, 255), 2)
            
            # 🔊 Play alert sound (once every 5 seconds)
            if time.time() - last_alert_time > alert_cooldown:
                winsound.Beep(1000, 700)  # (frequency, duration_ms)
                last_alert_time = time.time()
    else:
        # Reset timer when face is detected
        last_seen_time = time.time()

        # Draw rectangles around face and eyes
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            roi_gray = gray[y:y+h, x:x+w]
            roi_color = frame[y:y+h, x:x+w]
            eyes = eye_cascade.detectMultiScale(roi_gray)
            for (ex, ey, ew, eh) in eyes:
                cv2.rectangle(roi_color, (ex, ey), (ex+ew, ey+eh), (0, 255, 0), 2)

    # Display focus status
    cv2.putText(frame, "Focus Monitor Active", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

    cv2.imshow('Focus Detector', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
