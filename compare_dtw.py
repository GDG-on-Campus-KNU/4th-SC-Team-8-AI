import json
import numpy as np
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean
import sys

def extract_feature_sequence(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)
    
    frames_data = data.get("data", [])
    sequence = []
    for frame in frames_data:
        landmarks = frame.get("pose_landmarks")
        if landmarks:
            # 각 랜드마크의 x, y 좌표를 순서대로 추출
            feature_vector = []
            for lm in landmarks:
                # 각 값은 이미 0~1의 normalized 값으로 저장되어 있다고 가정합니다.
                feature_vector.append(lm.get("x", 0))
                feature_vector.append(lm.get("y", 0))
            sequence.append(np.array(feature_vector))
        else:
            # 데이터가 없는 프레임은 건너뛰거나, 필요에 따라 0벡터로 처리할 수 있음
            continue
    return sequence

if __name__ == "__main__":

    json_file1 = 'output/youtube_result/greeting_cam.json'
    json_file2 = 'output/youtube_result/greeting_original.json'

    seq1 = extract_feature_sequence(json_file1)
    seq2 = extract_feature_sequence(json_file2)

    if not seq1 or not seq2:
        print("하나 이상의 JSON 파일에서 유효한 프레임 데이터를 추출하지 못했습니다.")
        sys.exit(1)

    # DTW를 통해 두 시퀀스의 유사도(거리) 계산 (유클리드 거리를 사용)
    distance, path = fastdtw(seq1, seq2, dist=euclidean)
    print("DTW distance:", distance)