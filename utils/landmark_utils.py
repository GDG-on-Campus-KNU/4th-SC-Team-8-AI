import numpy as np

def landmark_list_to_dict(landmarks):
    """랜드마크를 딕셔너리 리스트로 변환"""
    if not landmarks:
        return None
    return [{"x": lm.x, "y": lm.y, "z": lm.z, "visibility": getattr(lm, 'visibility', 1.0)} for lm in landmarks]

# 참고: normalize_landmarks 함수는 이제 사용하지 않음
# 정규화는 점수 계산 시점에 similarity_compare_utils.py의 normalize_landmarks_array 함수로 처리됨