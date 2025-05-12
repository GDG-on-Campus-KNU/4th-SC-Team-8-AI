import numpy as np
import json
from fastdtw import fastdtw
from scipy.spatial.distance import cosine

# 1. 기존 safe_cosine_similarity 함수 개선
def safe_cosine_similarity(v1, v2):
    """
    개선된 코사인 유사도 계산
    기존 함수명을 유지하면서 정규화 및 범위 조정 추가
    """
    # 벡터 정규화
    v1_norm = np.linalg.norm(v1)
    v2_norm = np.linalg.norm(v2)
    
    if v1_norm == 0 or v2_norm == 0:
        return 0.0
    
    # 정규화된 벡터로 코사인 유사도 계산
    dot_product = np.dot(v1, v2)
    similarity = dot_product / (v1_norm * v2_norm)
    
    # -1 ~ 1 범위를 0 ~ 1 범위로 변환
    return (similarity + 1) / 2

# 2. 내부적으로 사용할 정규화 함수
def _normalize_landmarks(vectors):
    """
    랜드마크 좌표를 정규화 (내부 함수)
    """
    normalized_vectors = []
    for vec in vectors:
        if len(vec) == 0:
            normalized_vectors.append(vec)
            continue
            
        # 벡터를 2D 점들로 재구성 (x, y 쌍)
        points = vec.reshape(-1, 2)
        
        # 중심점 계산 (평균 위치)
        center = np.mean(points, axis=0)
        
        # 중심점을 원점으로 이동
        centered_points = points - center
        
        # 스케일 정규화 (최대 거리로 나누기)
        max_distance = np.max(np.linalg.norm(centered_points, axis=1))
        if max_distance > 0:
            normalized_points = centered_points / max_distance
        else:
            normalized_points = centered_points
            
        normalized_vectors.append(normalized_points.flatten())
    
    return normalized_vectors

# 3. 내부적으로 사용할 동작 구간 추출 함수
def _extract_movement_segments(vectors, threshold=0.05):
    """
    실제 동작이 있는 구간만 추출 (내부 함수)
    """
    if len(vectors) < 2:
        return vectors
    
    movement_indices = []
    
    for i in range(1, len(vectors)):
        # 이전 프레임과의 변화량 계산
        diff = np.linalg.norm(vectors[i] - vectors[i-1])
        if diff > threshold:
            movement_indices.append(i)
    
    if not movement_indices:
        # 움직임이 감지되지 않으면 전체 시퀀스 반환
        return vectors
    
    # 동작 구간 전후로 여유 프레임 추가
    start_idx = max(0, movement_indices[0] - 5)
    end_idx = min(len(vectors), movement_indices[-1] + 5)
    
    return vectors[start_idx:end_idx]

# 4. 가중치 계산 함수
def _calculate_weights(similarities):
    """
    동작의 시작과 끝에 가중치 적용 (내부 함수)
    """
    weights = np.ones(len(similarities))
    if len(similarities) > 8:  # 충분히 긴 시퀀스만 가중치 적용
        quarter = len(similarities) // 4
        weights[:quarter] *= 1.2  # 시작 부분
        weights[-quarter:] *= 1.2  # 끝 부분
    return weights

# 5. 기존 fetch_reference_landmark 함수는 그대로 유지
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

# 6. 기존 fetch_user_landmark 함수는 그대로 유지
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

# 7. 기존 compare_landmark 함수 개선 (함수명 동일하게 유지)
def compare_landmark(reference_seq: list[np.ndarray], user_seq: list[np.ndarray]) -> float:
    """
    개선된 랜드마크 비교 함수
    기존 함수명과 인터페이스를 유지하면서 내부 로직 개선
    """
    if not reference_seq or not user_seq:
        return 0.0  # 점수가 의미 없을 경우

    # 1. 정규화 적용
    try:
        ref_normalized = _normalize_landmarks(reference_seq)
        user_normalized = _normalize_landmarks(user_seq)
    except Exception as e:
        print(f"정규화 중 오류 발생: {e}")
        # 정규화 실패 시 기존 방식으로 폴백
        ref_normalized = reference_seq
        user_normalized = user_seq
    
    # 2. 동작 구간 추출 (선택적)
    try:
        ref_movement = _extract_movement_segments(np.array(ref_normalized))
        user_movement = _extract_movement_segments(np.array(user_normalized))
    except Exception as e:
        print(f"동작 구간 추출 중 오류 발생: {e}")
        # 실패 시 정규화된 전체 시퀀스 사용
        ref_movement = ref_normalized
        user_movement = user_normalized

    # 3. DTW 정렬
    _, path = fastdtw(ref_movement, user_movement, dist=safe_cosine_similarity)

    # 4. 유사도 계산
    similarity_scores = []
    for i, j in path:
        # 인덱스 초과 방지
        if i >= len(ref_movement) or j >= len(user_movement):
            continue
        v1, v2 = ref_movement[i], user_movement[j]
        sim = safe_cosine_similarity(v1, v2)
        similarity_scores.append(sim)

    if not similarity_scores:
        return 0.0

    # 5. 가중치 적용하여 평균 계산
    try:
        weights = _calculate_weights(similarity_scores)
        average_similarity = np.average(similarity_scores, weights=weights)
    except Exception as e:
        print(f"가중치 계산 중 오류 발생: {e}")
        # 실패 시 일반 평균 사용
        average_similarity = np.mean(similarity_scores)

    return round(float(average_similarity), 4)

# 8. 기존 score_to_label 함수 개선 (함수명 동일하게 유지)
def score_to_label(score):
    """
    개선된 점수 라벨 함수
    좀 더 관대한 기준으로 조정
    """
    if score > 0.8:     # 기존 0.85에서 0.8로 낮춤
        return "perfect"
    elif score > 0.65:  # 기존 0.7에서 0.65로 낮춤
        return "great"
    elif score > 0.45:  # 기존 0.5에서 0.45로 낮춤
        return "good"
    else:
        return "bad"

# 9. 디버깅용 함수 (선택적)
def debug_score_calculation(reference_seq, user_seq):
    """
    점수 계산 과정을 상세히 로그로 출력
    """
    print("=== 점수 계산 디버그 정보 ===")
    print(f"참조 시퀀스 길이: {len(reference_seq)}")
    print(f"사용자 시퀀스 길이: {len(user_seq)}")
    
    # 정규화 전 샘플 확인
    if reference_seq and user_seq:
        print(f"정규화 전 참조 샘플: {reference_seq[0][:5]}...")
        print(f"정규화 전 사용자 샘플: {user_seq[0][:5]}...")
    
    # 정규화 후 샘플 확인
    try:
        ref_norm = _normalize_landmarks(reference_seq)
        user_norm = _normalize_landmarks(user_seq)
        if ref_norm and user_norm:
            print(f"정규화 후 참조 샘플: {ref_norm[0][:5]}...")
            print(f"정규화 후 사용자 샘플: {user_norm[0][:5]}...")
    except Exception as e:
        print(f"정규화 중 오류: {e}")
    
    # 실제 점수 계산
    score = compare_landmark(reference_seq, user_seq)
    label = score_to_label(score)
    
    print(f"최종 점수: {score}")
    print(f"라벨: {label}")
    print("===========================")
    
    return score, label