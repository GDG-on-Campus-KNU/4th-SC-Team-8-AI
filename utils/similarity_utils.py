"""
랜드마크 기반 시퀀스 생성 & DTW 유사도 계산
"""
from __future__ import annotations

import cv2
import numpy as np
import mediapipe as mp
from typing import List, Dict, Sequence
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean


# --------------------------------------------------
# 1) JSON 프레임 → 벡터
# --------------------------------------------------
def _vectorize_pose(frame: Dict) -> np.ndarray | None:
    pose = frame.get("pose_landmarks") or []
    if not pose:
        return None
    vec: List[float] = []
    for lm in pose:
        vec.extend([lm["x"], lm["y"]])
    return np.asarray(vec, dtype=np.float32)


# --------------------------------------------------
# 2) 구간 필터링 → 시퀀스
# --------------------------------------------------
def build_sequence(
    frames: Sequence[Dict],
    start_ms: int,
    end_ms: int,
) -> List[np.ndarray]:
    seq: List[np.ndarray] = []
    for fr in frames:
        ts = fr.get("timestamp_ms", 0)
        if start_ms <= ts <= end_ms:
            v = _vectorize_pose(fr)
            if v is not None:
                seq.append(v)
    return seq


# --------------------------------------------------
# 3) 업로드 영상에서 랜드마크 시퀀스 추출
# --------------------------------------------------
def extract_landmark_sequence_from_video(
    video_path: str,
    max_frames: int = 300,
) -> List[np.ndarray]:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return []

    mp_pose = mp.solutions.pose.Pose(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
    )

    seq: List[np.ndarray] = []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    frame_idx = 0
    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = mp_pose.process(rgb)
        if res.pose_landmarks:
            vec = []
            for lm in res.pose_landmarks.landmark:
                vec.extend([lm.x, lm.y])
            seq.append(np.asarray(vec, dtype=np.float32))

    cap.release()
    mp_pose.close()
    return seq


# --------------------------------------------------
# 4) DTW 유사도 & 등급
# --------------------------------------------------
def similarity(
    seq_ref: List[np.ndarray],
    seq_test: List[np.ndarray],
) -> float:
    """DTW 거리 (작을수록 유사)"""
    if not seq_ref or not seq_test:
        return float("inf")
    dist, _ = fastdtw(seq_ref, seq_test, dist=euclidean)
    return dist


def rating(dist: float) -> str:
    if dist == float("inf"):
        return "no_data"
    if dist < 50:
        return "perfect"
    if dist < 120:
        return "great"
    return "good"
