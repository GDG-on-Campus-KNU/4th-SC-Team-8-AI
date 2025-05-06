from __future__ import annotations

import cv2
import numpy as np
import mediapipe as mp
import math
from typing import List, Dict, Sequence
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

# --------------------------------------------------
# 1) JSON 프레임 → 양손 벡터 (손 랜드마크만)
# --------------------------------------------------
def _vectorize_hands(frame: Dict) -> np.ndarray | None:
    left = frame.get("left_hand_landmarks") or []
    right = frame.get("right_hand_landmarks") or []
    if not left and not right:
        return None

    vec: List[float] = []
    for lm in left:
        vec.extend([lm["x"], lm["y"]])
    for lm in right:
        vec.extend([lm["x"], lm["y"]])

    # 없는 쪽은 0으로 패딩
    if len(left) < 21:
        vec.extend([0.0, 0.0] * (21 - len(left)))
    if len(right) < 21:
        vec.extend([0.0, 0.0] * (21 - len(right)))

    return np.asarray(vec, dtype=np.float32)

# --------------------------------------------------
# 2) 구간 필터링 → 시퀀스
# --------------------------------------------------
def build_sequence(
    frames: Sequence[Dict],
    start_ms: int,
    end_ms: int,
) -> List[np.ndarray]:
    print("start ms :",  start_ms)
    print("end ms :",  end_ms)
    seq: List[np.ndarray] = []
    for fr in frames:
        ts = fr.get("timestamp_ms", 0)
        if start_ms <= ts <= end_ms:
            v = _vectorize_hands(fr)
            if v is not None:
                seq.append(v)
    return seq

# --------------------------------------------------
# 3) 업로드 영상 → 랜드마크 시퀀스 (손만)
# --------------------------------------------------
def extract_landmark_sequence_from_video(
    video_path: str,
    max_frames: int = 300,
) -> List[np.ndarray]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []
    mp_hands = mp.solutions.hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        model_complexity=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    seq: List[np.ndarray] = []
    idx = 0
    while idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        idx += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = mp_hands.process(rgb)
        left_lm, right_lm = [], []
        if res.multi_hand_landmarks:
            for hand_landmarks, handedness in zip(res.multi_hand_landmarks, res.multi_handedness):
                pts = [{"x": lm.x, "y": lm.y} for lm in hand_landmarks.landmark]
                if handedness.classification[0].label == "Left":
                    left_lm = pts
                else:
                    right_lm = pts
        frame_dict = {
            "left_hand_landmarks": left_lm,
            "right_hand_landmarks": right_lm,
        }
        v = _vectorize_hands(frame_dict)
        if v is not None:
            seq.append(v)

    cap.release()
    mp_hands.close()
    return seq

# --------------------------------------------------
# 4) 유사도 계산 (정적+동적 패턴 반영)
# --------------------------------------------------
def similarity(
    seq_ref: List[np.ndarray],
    seq_test: List[np.ndarray],
    motion_weight: float = 0.5
) -> float:
    """손 랜드마크 DTW + 움직임 패턴 반영: 0~100 점수 반환"""
    if not seq_ref or not seq_test:
        return 0.0

    # 2프레임 단위 샘플링
    step = 2
    ref_s = [seq_ref[i] for i in range(0, len(seq_ref), step)]
    test_s = [seq_test[i] for i in range(0, len(seq_test), step)]
    if not ref_s or not test_s:
        return 0.0

    # 벡터 차원 및 이론적 최대 거리
    D = ref_s[0].shape[0]
    max_dist = math.sqrt(2 * D)

    # 1) 정적 자세 DTW 거리
    dist_shape, _ = fastdtw(ref_s, test_s, dist=euclidean)
    length = min(len(ref_s), len(test_s))
    avg_dist_shape = dist_shape / length if length > 0 else float('inf')
    shape_norm = avg_dist_shape / max_dist

    # 2) 동적 패턴 (속도) DTW 거리
    #    velocity vectors: 프레임 간 차이
    ref_v = [ref_s[i] - ref_s[i-1] for i in range(1, len(ref_s))]
    test_v = [test_s[i] - test_s[i-1] for i in range(1, len(test_s))]
    length_v = min(len(ref_v), len(test_v))
    if length_v > 0:
        dist_vel, _ = fastdtw(ref_v, test_v, dist=euclidean)
        avg_dist_vel = dist_vel / length_v
        vel_norm = avg_dist_vel / max_dist
    else:
        vel_norm = 1.0  # 움직임 정보가 없으면 최대 거리 가정

    # 3) 정규화된 두 거리의 가중합
    combined_norm = (1 - motion_weight) * shape_norm + motion_weight * vel_norm

    # 4) 점수 변환
    score = max(0.0, (1 - combined_norm)) * 100
    return score

# --------------------------------------------------
# 5) 등급 매핑
# --------------------------------------------------
def rating_from_dist(score: float) -> str:
    if score >= 90:
        return "perfect"
    elif score >= 70:
        return "great"
    elif score >= 40:
        return "good"
    else:
        return "bad"

# legacy alias
def rating(score: float) -> str:
    return rating_from_dist(score)
