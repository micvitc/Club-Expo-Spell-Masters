import math

def get_embedding(landmark_list):
    """
    Converts a mediapipe landmark list into a robust 72-dimensional vector embedding.
    Captures overall shape, finger openness, and finger spread.
    """
    if not landmark_list: return None
    
    # Handle both MediaPipe landmark objects and dictionaries
    is_dict = isinstance(landmark_list[0], dict)
    
    def get_coords(lm):
        if is_dict: return lm['x'], lm['y'], lm['z']
        else: return lm.x, lm.y, lm.z

    wrist_x, wrist_y, wrist_z = get_coords(landmark_list[0])
    
    # 1. Translate relative to wrist
    translated = []
    for lm in landmark_list:
        x, y, z = get_coords(lm)
        translated.append([x - wrist_x, y - wrist_y, z - wrist_z])
        
    # 2. Scale normalization (divide by max distance from wrist)
    max_dist = 0
    for x, y, z in translated:
        dist = math.sqrt(x**2 + y**2 + z**2)
        if dist > max_dist: max_dist = dist
        
    if max_dist == 0: max_dist = 1.0
    
    scaled = [[x/max_dist, y/max_dist, z/max_dist] for x, y, z in translated]
    
    # 3. Build embedding vector
    vector = []
    # Base 63 features (overall shape & orientation)
    for pt in scaled:
        vector.extend(pt)
        
    # 5 features: Fingertip to wrist distance (Are fingers open or closed?)
    # Index 4=Thumb, 8=Index, 12=Middle, 16=Ring, 20=Pinky
    fingertips = [4, 8, 12, 16, 20]
    for tip in fingertips:
        dist = math.sqrt(scaled[tip][0]**2 + scaled[tip][1]**2 + scaled[tip][2]**2)
        vector.append(dist)
        
    # 4 features: Distance between adjacent fingertips (Are fingers spread apart?)
    for i in range(len(fingertips) - 1):
        t1, t2 = fingertips[i], fingertips[i+1]
        dist = math.sqrt((scaled[t1][0]-scaled[t2][0])**2 + 
                         (scaled[t1][1]-scaled[t2][1])**2 + 
                         (scaled[t1][2]-scaled[t2][2])**2)
        vector.append(dist)
        
    # 4. L2 Normalize the final embedding vector for Cosine Similarity
    mag = math.sqrt(sum(v**2 for v in vector))
    if mag > 0:
        vector = [v/mag for v in vector]
        
    return vector

def calculate_similarity(v1, v2):
    """
    Calculates cosine similarity between two embedding vectors.
    Returns a percentage (0 to 100).
    """
    if not v1 or not v2 or len(v1) != len(v2): return 0
    
    dot_product = sum(a * b for a, b in zip(v1, v2))
    
    # Cosine similarity ranges from -1 to 1. 
    # For robust hand gestures, anything below 0.85 is usually a completely different gesture.
    # We will map 0.85 -> 0% and 1.0 -> 100% to make it intuitive.
    floor = 0.85
    if dot_product < floor:
        return 0
    
    percentage = ((dot_product - floor) / (1.0 - floor)) * 100
    return max(0, min(100, int(percentage)))
