import cv2
import mediapipe as mp
import json
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
            
            live_embedding = get_embedding(hand_landmarks.landmark)

            current_percentages = {}
            best_match_name = "None"
            best_match_percentage = 0
            
            for name, embeddings_list in gestures_db.items():
                best_variant_percentage = 0
                for saved_embedding in embeddings_list:
                    pct = calculate_similarity(live_embedding, saved_embedding)
                    if pct > best_variant_percentage:
                        best_variant_percentage = pct
                        
                current_percentages[name] = best_variant_percentage
                
                if best_variant_percentage > best_match_percentage:
                    best_match_percentage = best_variant_percentage
                    best_match_name = name

            if best_match_percentage >= CONFIDENCE_THRESHOLD:
                display_text = f"DETECTED: {best_match_name} ({best_match_percentage}%)"
                text_color = (0, 255, 0)
            else:
                display_text = f"DETECTED: None (Best: {best_match_name} {best_match_percentage}%)"
                text_color = (0, 0, 255)

            cv2.putText(frame, display_text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, text_color, 2)
            
            y_offset = 80
            cv2.putText(frame, "Confidence Scores:", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
            
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
