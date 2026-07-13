import cv2
import mediapipe as mp
import json
import math
import threading
import uvicorn
import asyncio
from fastapi import FastAPI, WebSocket

app = FastAPI()

current_state = {
    "gesture": "None",
    "accuracy": 0
}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_text(json.dumps(current_state))
            await asyncio.sleep(0.1) 
    except Exception:
        pass

def start_api():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")

api_thread = threading.Thread(target=start_api, daemon=True)
api_thread.start()

try:
    with open("gestures.json", "r") as f:
        gestures_db = json.load(f)
except Exception:
    exit()

if not gestures_db:
    exit()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils
cap = cv2.VideoCapture(0)

MAX_TOLERANCE = 0.15 
MATCH_THRESHOLD = 60

while True:
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    recognized_gesture = "None"
    best_accuracy = 0

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            
            live_landmarks = [{'x': lm.x, 'y': lm.y, 'z': lm.z} for lm in hand_landmarks.landmark]
            live_wrist = live_landmarks[0]
            norm_live = [
                {'x': lm['x'] - live_wrist['x'], 'y': lm['y'] - live_wrist['y'], 'z': lm['z'] - live_wrist['z']}
                for lm in live_landmarks
            ]

            for name, s_landmarks in gestures_db.items():
                total_distance = 0
                for i in range(21):
                    dx = norm_live[i]['x'] - s_landmarks[i]['x']
                    dy = norm_live[i]['y'] - s_landmarks[i]['y']
                    dz = norm_live[i]['z'] - s_landmarks[i]['z']
                    total_distance += math.sqrt(dx**2 + dy**2 + dz**2)
                
                average_error = total_distance / 21
                raw_percentage = (1 - (average_error / MAX_TOLERANCE)) * 100
                accuracy = max(0, int(raw_percentage))
                
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    recognized_gesture = name

            if best_accuracy >= MATCH_THRESHOLD:
                current_state["gesture"] = recognized_gesture
                current_state["accuracy"] = best_accuracy
                cv2.putText(frame, f"{recognized_gesture} {best_accuracy}%", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            else:
                current_state["gesture"] = "None"
                current_state["accuracy"] = best_accuracy
                cv2.putText(frame, "None", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    else:
        current_state["gesture"] = "None"
        current_state["accuracy"] = 0

    cv2.imshow("Cam", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
