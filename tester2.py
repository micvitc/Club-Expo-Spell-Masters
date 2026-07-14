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
CONFIDENCE_THRESHOLD = 60 # Minimum % to declare a gesture detected

print("\n==== Continuous Auto-Tester ====")
print("Running continuously. Perform any saved gesture.")
print("Press 'q' to quit.")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(rgb_frame)

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
            best_match_name = "None"
            best_match_percentage = 0
            
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
                
                # Check if this is the overall best match
                if best_variant_percentage > best_match_percentage:
                    best_match_percentage = best_variant_percentage
                    best_match_name = name

            # Display the best match prominently
            if best_match_percentage >= CONFIDENCE_THRESHOLD:
                display_text = f"DETECTED: {best_match_name} ({best_match_percentage}%)"
                text_color = (0, 255, 0) # Green for high confidence
            else:
                display_text = f"DETECTED: None (Best: {best_match_name} {best_match_percentage}%)"
                text_color = (0, 0, 255) # Red for low confidence

            cv2.putText(frame, display_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
            
            # Display all gesture percentages below
            y_offset = 80
            cv2.putText(frame, "Confidence Scores:", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
            # Sort percentages descending
            sorted_percentages = sorted(current_percentages.items(), key=lambda x: x[1], reverse=True)
            for name, pct in sorted_percentages:
                y_offset += 25
                txt_color = (0, 255, 255) if pct >= CONFIDENCE_THRESHOLD else (200, 200, 200)
                cv2.putText(frame, f"- {name}: {pct}%", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, txt_color, 1)

    cv2.imshow("Continuous Auto-Tester", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("Testing aborted.")
        break

cap.release()
cv2.destroyAllWindows()
