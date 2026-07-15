import cv2
import mediapipe as mp
import json
import threading
import time
from gesture_utils import get_embedding, calculate_similarity

class AsyncGestureDetector(threading.Thread):
    def __init__(self, db_path="gestures.json", callback=None, threshold=60, cooldown=2.0):
        super().__init__()
        self.db_path = db_path
        self.callback = callback
        self.threshold = threshold
        self.cooldown = cooldown
        self.running = False
        self.gestures_db = {}
        self.last_detection_time = {}
        
        try:
            with open(self.db_path, "r") as f:
                self.gestures_db = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            print("Error: Gesture database not found or invalid.")
            
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(static_image_mode=False, max_num_hands=1, min_detection_confidence=0.7)
        
    def stop(self):
        self.running = False
        
    def run(self):
        if not self.gestures_db:
            print("No gestures in database. Background detector exiting.")
            return
            
        self.running = True
        cap = cv2.VideoCapture(0)
        
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret: break

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    live_embedding = get_embedding(hand_landmarks.landmark)

                    best_match_name = None
                    best_match_percentage = 0

                    for saved_name, embeddings_list in self.gestures_db.items():
                        for saved_embedding in embeddings_list:
                            pct = calculate_similarity(live_embedding, saved_embedding)
                            if pct > best_match_percentage:
                                best_match_percentage = pct
                                best_match_name = saved_name

                    if best_match_name and best_match_percentage >= self.threshold:
                        current_time = time.time()
                        last_time = self.last_detection_time.get(best_match_name, 0)
                        
                        if current_time - last_time > self.cooldown:
                            self.last_detection_time[best_match_name] = current_time
                            if self.callback:
                                self.callback(best_match_name, best_match_percentage)

        cap.release()

# --- Main Program ---
def on_gesture_detected(gesture_name, accuracy):
    """
    This callback is triggered asynchronously from the detector thread 
    whenever a valid gesture is recognized.
    """
    print(f"\n[ASYNC EVENT] Gesture '{gesture_name}' detected with {accuracy}% accuracy!")
    
    if gesture_name == "fireball":
        print(">> Casting Fireball! <<")
    elif gesture_name == "shield":
        print(">> Activating Shield! <<")

if __name__ == "__main__":
    print("Starting background gesture detector...")
    
    detector = AsyncGestureDetector(callback=on_gesture_detected, threshold=70, cooldown=2.0)
    detector.start()
    
    try:
        while True:
            print("Main program loop is doing other work...")
            time.sleep(2)
    except KeyboardInterrupt:
        print("Shutting down...")
        detector.stop()
        detector.join()
