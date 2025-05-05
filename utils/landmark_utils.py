def landmark_list_to_dict(landmarks):
    if hasattr(landmarks, "landmark"):
        landmarks = landmarks.landmark
    return [
        {"x": lm.x, "y": lm.y, "z": lm.z, "visibility": lm.visibility}
        for lm in landmarks
    ]


def normalize_landmarks(landmarks):
    # 코(0번)의 위치를 (0,0) 으로 평행이동, 어깨-폭으로 스케일 정규화 예시
    if not landmarks:
        return landmarks
    ref = landmarks[0]           # 코
    offset_x, offset_y = -ref["x"], -ref["y"]
    # 스케일 기준은 어깨 간 거리 등…  여기선 1 로 두고 필드만 dict식으로 수정
    scale = 1.0

    for lm in landmarks:
        lm["x"] = (lm["x"] + offset_x) * scale
        lm["y"] = (lm["y"] + offset_y) * scale
        lm["z"] = lm["z"] * scale
    return landmarks
