import cv2
import mediapipe as mp
import json
import os
from gesture_utils import get_embedding

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

print("==== Gesture Saver (Vector Embeddings) ====")
print("Press 's' to save a gesture.")
print("Tip: You can save multiple slight variations of the same gesture under the same name!")
print("Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

    landmark_list = None

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            landmark_list = hand_landmarks.landmark

    cv2.imshow("Save Gestures", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('s') and landmark_list:
        gesture_name = input("\n> Enter a name for this gesture: ")
        
        embedding = get_embedding(landmark_list)
        
        if gesture_name not in gestures_db:
            gestures_db[gesture_name] = []
            
        gestures_db[gesture_name].append(embedding)
        
        with open(db_file, "w") as f:
            json.dump(gestures_db, f, indent=4)
            
        print(f"Saved variation #{len(gestures_db[gesture_name])} for '{gesture_name}' successfully!")

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
