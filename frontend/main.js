// frontend/main.js — MediaPipe FaceMesh + EAR detection + working alarm

const video = document.getElementById('video');
const canvas = document.getElementById('capture-canvas');
const startBtn = document.getElementById('start-camera');
const stopBtn = document.getElementById('stop-camera');
const fpsSelect = document.getElementById('fps-select');
const socketStatus = document.getElementById('socket-status');
const srvResp = document.getElementById('srv-resp');
const detectStatus = document.getElementById('detect-status');
const alarm = document.getElementById('alarm');

let socket = null;
let sendInterval = null;
let mpCamera = null;
let sendingToServer = true;

// ---------- SOCKET.IO SETUP ----------
function setupSocket() {
  socket = io("http://127.0.0.1:5000");
  socket.on('connect', () => {
    socketStatus.innerText = 'connected';
    console.log('socket connected');
  });
  socket.on('disconnect', () => {
    socketStatus.innerText = 'disconnected';
    console.log('socket disconnected');
  });
  socket.on('status', (data) => {
    srvResp.innerText = JSON.stringify(data, null, 2);
  });
  socket.on('ack', (d) => { console.log('ack', d); });
}
setupSocket();

// ---------- MATH HELPERS ----------
function dist(a, b) {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.hypot(dx, dy);
}

// ---------- EAR CALCULATION ----------
const LEFT_EYE_IDX = [33, 160, 158, 133, 153, 144];
const RIGHT_EYE_IDX = [263, 387, 385, 362, 380, 373];

function computeEAR(landmarks, eyeIdx) {
  const p1 = landmarks[eyeIdx[0]];
  const p2 = landmarks[eyeIdx[1]];
  const p3 = landmarks[eyeIdx[2]];
  const p4 = landmarks[eyeIdx[3]];
  const p5 = landmarks[eyeIdx[4]];
  const p6 = landmarks[eyeIdx[5]];
  const A = dist(p2, p6);
  const B = dist(p3, p5);
  const C = dist(p1, p4);
  if (C === 0) return 0;
  return (A + B) / (2.0 * C);
}

// ---------- DETECTION STATE ----------
let eyeClosedStart = null;
let distractedSince = null;
const EYE_CLOSED_SECONDS = 2.0;
let EAR_THRESHOLD = 0.21; // tune if needed

// ---------- MEDIAPIPE FACEMESH ----------
const faceMesh = new FaceMesh({
  locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`
});
faceMesh.setOptions({
  maxNumFaces: 1,
  refineLandmarks: true,
  minDetectionConfidence: 0.5,
  minTrackingConfidence: 0.5
});
faceMesh.onResults(onFaceResults);

async function startCameraMP() {
  if (mpCamera) return;
  mpCamera = new Camera(video, {
    onFrame: async () => { await faceMesh.send({ image: video }); },
    width: 640,
    height: 480
  });
  mpCamera.start();
}

function stopCameraMP() {
  if (!mpCamera) return;
  mpCamera.stop();
  mpCamera = null;
}

// ---------- FACEMESH CALLBACK ----------
function onFaceResults(results) {
  if (!results || !results.multiFaceLandmarks || results.multiFaceLandmarks.length === 0) {
    detectStatus.innerText = 'no face';
    eyeClosedStart = null;
    distractedSince = null;
    sendingToServer = true;
    return;
  }

  const lm = results.multiFaceLandmarks[0];
  const leftEAR = computeEAR(lm, LEFT_EYE_IDX);
  const rightEAR = computeEAR(lm, RIGHT_EYE_IDX);
  const ear = (leftEAR + rightEAR) / 2.0;
  detectStatus.innerText = `EAR: ${ear.toFixed(3)}`;

  const now = performance.now() / 1000.0;
  if (ear < EAR_THRESHOLD) {
    if (!eyeClosedStart) eyeClosedStart = now;
    const closedFor = now - eyeClosedStart;
    if (closedFor > EYE_CLOSED_SECONDS) {
      detectStatus.innerText = `DISTRACTED (sleep) — ${closedFor.toFixed(1)}s`;
      if (!distractedSince) {
        distractedSince = now;
        try {
          alarm.currentTime = 0;
          alarm.play().catch(err => console.warn("⚠️ Alarm play failed:", err));
        } catch (e) {
          console.warn("Alarm error:", e);
        }
        if (socket && socket.connected) {
          socket.emit('detection', { type: 'eyes_closed', duration: closedFor, ts: Date.now() });
        }
      }
      sendingToServer = false;
    }
  } else {
    if (distractedSince) {
      const recoveredAfter = now - distractedSince;
      console.log('Recovered after', recoveredAfter);
      if (socket && socket.connected) {
        socket.emit('detection', { type: 'recovered', duration: recoveredAfter, ts: Date.now() });
      }
    }
    eyeClosedStart = null;
    distractedSince = null;
    sendingToServer = true;
  }
}

// ---------- START BUTTON ----------
startBtn.addEventListener('click', async () => {
  // 🔊 Unlock audio
  try {
    alarm.muted = false;
    alarm.volume = 1.0;
    const p = alarm.play();
    if (p !== undefined) {
      p.then(() => {
        alarm.pause();
        alarm.currentTime = 0;
        console.log("✅ Audio unlocked for alarm.");
      }).catch(err => {
        console.warn("⚠️ Audio unlock failed:", err);
      });
    }
  } catch (e) {
    console.warn("Audio unlock error:", e);
  }

  // Start camera + frame sending
  try {
    await startCameraMP();
    document.getElementById('session-info').innerText = 'Session: camera started (MediaPipe)';
    startSendingFrames();
  } catch (err) {
    console.error('Camera start error', err);
    alert('Camera permission denied or not available.');
  }
});

// ---------- STOP BUTTON ----------
stopBtn.addEventListener('click', () => {
  stopSendingFrames();
  stopCameraMP();
  document.getElementById('session-info').innerText = 'Session: camera stopped';
});

// ---------- FRAME SENDING ----------
function startSendingFrames() {
  stopSendingFrames();
  const fps = Number(fpsSelect.value) || 1;
  const intervalMs = Math.round(1000 / fps);
  sendInterval = setInterval(() => {
    if (video.readyState !== 4) return;
    if (!sendingToServer) return;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.6);
    if (socket && socket.connected) socket.emit('frame', dataUrl);
  }, intervalMs);
}

function stopSendingFrames() {
  if (sendInterval) { clearInterval(sendInterval); sendInterval = null; }
}

// ---------- CLEANUP ----------
window.addEventListener('beforeunload', () => {
  stopSendingFrames();
  stopCameraMP();
});


