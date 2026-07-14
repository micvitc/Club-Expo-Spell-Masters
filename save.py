import cv2
import mediapipe as mp
import json
import os

db_file = "gestures.json"
if os.path.exists(db_file):
    with open(db_file, "r") as f:
        try:
            gestures_db = json.load(f)
        except json.JSONDecodeError:
            gestures_db = {}
else:
    gestures_db = {}

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    landmark_list = []

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            for lm in hand_landmarks.landmark:
                landmark_list.append({'x': lm.x, 'y': lm.y, 'z': lm.z})

    cv2.imshow("Save Multiple Gestures", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('s') and landmark_list:
        gesture_name = input("\n> Enter a name for this gesture: ")
        
        wrist = landmark_list[0]
        normalized_landmarks = [
            {'x': lm['x'] - wrist['x'], 'y': lm['y'] - wrist['y'], 'z': lm['z'] - wrist['z']}
            for lm in landmark_list
        ]
        
        # Generate 16 rotated orientations (every 22.5 degrees) to make it rotation-invariant
        multi_orientations = []
        import math
        for i in range(16):
            angle_rad = i * (2 * math.pi / 16)
            cos_a = math.cos(angle_rad)
            sin_a = math.sin(angle_rad)
            
            rotated_lm = []
            for lm in normalized_landmarks:
                # Rotate x,y around wrist (0,0)
                nx = lm['x'] * cos_a - lm['y'] * sin_a
                ny = lm['x'] * sin_a + lm['y'] * cos_a
                rotated_lm.append({'x': nx, 'y': ny, 'z': lm['z']})
            multi_orientations.append(rotated_lm)
            
        gestures_db[gesture_name] = multi_orientations
        
        with open(db_file, "w") as f:
            json.dump(gestures_db, f, indent=4)
            
        print(f"Saved '{gesture_name}' successfully!")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
