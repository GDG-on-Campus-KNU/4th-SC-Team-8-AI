import numpy as np

def landmark_list_to_dict(landmarks):
    """랜드마크를 딕셔너리 리스트로 변환"""
    if not landmarks:
        return None
    return [{"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility} for lm in landmarks]

def normalize_landmarks(landmarks, offset_x=0.0, offset_y=0.0):
    """랜드마크를 정규화"""
    if not landmarks:
        return []

    # 중앙 정렬
    for lm in landmarks:
        lm.x += offset_x
        lm.y += offset_y

    # 벡터 정규화
    xs = [lm.x for lm in landmarks]
    ys = [lm.y for lm in landmarks]
    vec = np.array(xs + ys)
    norm = np.linalg.norm(vec)

    if norm > 1e-8:
        for lm in landmarks:
            lm.x /= norm
            lm.y /= norm
