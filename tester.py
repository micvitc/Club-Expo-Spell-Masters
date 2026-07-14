import cv2
import mediapipe as mp
import json
import math
import time

try:
    with open("gestures.json", "r") as f:
        gestures_db = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    print("Error: 'gestures.json' not found or empty.")
    exit()

if not gestures_db:
    print("No gestures saved yet. Please run save.py to save some gestures first.")
    exit()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = cv2.VideoCapture(0)
MAX_TOLERANCE = 0.15 

leaderboard = {}

print("\n==== Welcome to the Gesture Tester! ====")
print("For each gesture, you will have 5 seconds to perform it.")

for target_gesture, saved_landmarks in gestures_db.items():
    print(f"\n>>> Get ready to perform: '{target_gesture}' in 3 seconds...")
    cv2.waitKey(3000)
    
    start_time = time.time()
    max_accuracy = 0
    
    while time.time() - start_time < 5:
        ret, frame = cap.read()
        if not ret: break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        display_text = f"Testing: {target_gesture} (Time left: {int(5 - (time.time() - start_time))}s)"
        color = (255, 255, 255)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                live_landmarks = [{'x': lm.x, 'y': lm.y, 'z': lm.z} for lm in hand_landmarks.landmark]
                live_wrist = live_landmarks[0]
                norm_live = [
                    {'x': lm['x'] - live_wrist['x'], 'y': lm['y'] - live_wrist['y'], 'z': lm['z'] - live_wrist['z']}
                    for lm in live_landmarks
                ]

                current_percentages = {}
                for name, s_landmarks_list in gestures_db.items():
                    # Backwards compatibility: if it's the old format (list of 21 dicts), wrap it in a list
                    if len(s_landmarks_list) > 0 and isinstance(s_landmarks_list[0], dict):
                        s_landmarks_list = [s_landmarks_list]
                        
                    best_variant_percentage = 0
                    for s_landmarks in s_landmarks_list:
                        total_distance = 0
                        for i in range(21):
                            dx = norm_live[i]['x'] - s_landmarks[i]['x']
                            dy = norm_live[i]['y'] - s_landmarks[i]['y']
                            dz = norm_live[i]['z'] - s_landmarks[i]['z']
                            total_distance += math.sqrt(dx**2 + dy**2 + dz**2)
                        
                        average_error = total_distance / 21
                        raw_percentage = (1 - (average_error / MAX_TOLERANCE)) * 100
                        percentage = max(0, int(raw_percentage))
                        
                        if percentage > best_variant_percentage:
                            best_variant_percentage = percentage
                            
                    current_percentages[name] = best_variant_percentage
                
                target_percentage = current_percentages.get(target_gesture, 0)
                if target_percentage > max_accuracy:
                    max_accuracy = target_percentage

                cv2.putText(frame, f"Target '{target_gesture}': {target_percentage}%", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0) if target_percentage > 70 else (0,0,255), 2)
                
                y_offset = 120
                cv2.putText(frame, "All Gestures (Check Overlap):", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                for name, pct in current_percentages.items():
                    y_offset += 25
                    txt_color = (0, 255, 255) if pct > 60 else (200, 200, 200)
                    cv2.putText(frame, f"- {name}: {pct}%", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, txt_color, 1)

        cv2.putText(frame, display_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        cv2.imshow("Gesture Tester", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("Testing aborted.")
            cap.release()
            cv2.destroyAllWindows()
            exit()
            
    print(f"Max accuracy for '{target_gesture}': {max_accuracy}%")
    leaderboard[target_gesture] = max_accuracy

cap.release()
cv2.destroyAllWindows()

print("\n==== LEADERBOARD ====")
sorted_leaderboard = sorted(leaderboard.items(), key=lambda item: item[1], reverse=True)
for i, (name, accuracy) in enumerate(sorted_leaderboard):
    print(f"{i+1}. {name}: {accuracy}%")
