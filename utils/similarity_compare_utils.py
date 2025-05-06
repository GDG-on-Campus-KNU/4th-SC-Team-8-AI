import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import cosine

# 코사인 유사도 안전 계산
def safe_cosine_similarity(v1, v2):
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return 1 - cosine(v1, v2)

import numpy as np
import json
from fastdtw import fastdtw
from scipy.spatial.distance import cosine

# 안전한 코사인 유사도 계산
def safe_cosine_similarity(v1, v2):
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0:
        return 0.0
    return 1 - cosine(v1, v2)

def fetch_reference_landmark(start_ms: int, end_ms: int, reference_data: dict) -> list[np.ndarray]:
    frames = reference_data.get("data", [])
    selected = [
        frame for frame in frames
        if start_ms <= frame.get("timestamp_ms", 0) <= end_ms
    ]
    
    vectors = []
    json_log = []

    for frame in selected:
        vec = []
        left_hand = frame.get("left_hand_landmarks") or []
        right_hand = frame.get("right_hand_landmarks") or []

        for hand in [left_hand, right_hand]:
            for lm in hand:
                vec.extend([lm.get("x", 0), lm.get("y", 0)])
            if len(hand) < 21:
                vec.extend([0.0, 0.0] * (21 - len(hand)))

        vectors.append(np.array(vec))

        json_log.append({
            "frame": frame.get("frame", -1),
            "left_hand_landmarks": left_hand,
            "right_hand_landmarks": right_hand
        })

    with open("reference_output.json", "w", encoding="utf-8") as f:
        json.dump(json_log, f, ensure_ascii=False, indent=2)
    
    return vectors

def fetch_user_landmark(user_landmarks: list[dict]) -> list[np.ndarray]:
    vectors = []
    json_log = []

    for frame in user_landmarks:
        vec = []
        left_hand = frame.get("left_hand_landmarks") or []
        right_hand = frame.get("right_hand_landmarks") or []

        for hand in [left_hand, right_hand]:
            for lm in hand:
                vec.extend([lm.get("x", 0), lm.get("y", 0)])
            if len(hand) < 21:
                vec.extend([0.0, 0.0] * (21 - len(hand)))

        vectors.append(np.array(vec))

        json_log.append({
            "frame": frame.get("frame", -1),
            "left_hand_landmarks": left_hand,
            "right_hand_landmarks": right_hand
        })

    with open("user_output.json", "w", encoding="utf-8") as f:
        json.dump(json_log, f, ensure_ascii=False, indent=2)

    return vectors

def compare_landmark(reference_seq: list[np.ndarray], user_seq: list[np.ndarray]) -> float:
    if not reference_seq or not user_seq:
        return 0.0  # 점수가 의미 없을 경우

    _, path = fastdtw(reference_seq, user_seq, dist=safe_cosine_similarity)

    similarity_scores = []
    for i, j in path:
        # 인덱스 초과 방지
        if i >= len(reference_seq) or j >= len(user_seq):
            continue
        v1, v2 = reference_seq[i], user_seq[j]
        sim = safe_cosine_similarity(v1, v2)
        similarity_scores.append(sim)

    if not similarity_scores:
        return 0.0

    average_similarity = np.mean(similarity_scores)
    return round(float(average_similarity), 4)

def score_to_label(score):
    if score > 0.85:
        return "perfect"
    elif score > 0.7:
        return "great"
    elif score > 0.5:
        return "good"
    else:
        return "bad"