import cv2
import mediapipe as mp
import json
import time
from gesture_utils import get_embedding, calculate_similarity

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

leaderboard = {}

print("\n==== Welcome to the Gesture Tester! ====")
print("For each gesture, you will have 5 seconds to perform it.")

for target_gesture, saved_embeddings in gestures_db.items():
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
                
                live_embedding = get_embedding(hand_landmarks.landmark)

                current_percentages = {}
                for name, embeddings_list in gestures_db.items():
                    best_variant_percentage = 0
                    for saved_embedding in embeddings_list:
                        pct = calculate_similarity(live_embedding, saved_embedding)
                        if pct > best_variant_percentage:
                            best_variant_percentage = pct
                            
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
