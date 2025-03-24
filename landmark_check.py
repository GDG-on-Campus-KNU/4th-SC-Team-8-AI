import cv2
import json
import os
import sys
import numpy as np

def draw_landmarks(frame, landmarks, color=(0, 255, 0), radius=5):
    """
    주어진 frame 위에, 랜드마크 리스트의 normalized 좌표(0~1)를
    영상의 픽셀 좌표로 변환하여 원형으로 표시합니다.
    """
    if landmarks is None:
        return
    height, width, _ = frame.shape
    for lm in landmarks:
        # normalized 좌표를 실제 픽셀 좌표로 변환
        x = int(lm["x"] * width)
        y = int(lm["y"] * height)
        cv2.circle(frame, (x, y), radius, color, -1)

def display_landmarks_from_json(json_path, window_size=(1280, 720), delay=30):
    """
    주어진 JSON 파일에서 프레임별 랜드마크 데이터를 읽어,
    빈 검은 화면(주어진 window_size) 위에 오버레이하여 순차적으로 표시합니다.
    delay: 각 프레임을 표시하는 시간(ms)
    """
    if not os.path.exists(json_path):
        print(f"JSON 파일이 존재하지 않습니다: {json_path}")
        return

    # JSON 파일 로드
    with open(json_path, "r") as f:
        data = json.load(f)
    
    frames_data = data.get("data", [])
    total_frames = len(frames_data)
    if total_frames == 0:
        print("JSON에 저장된 프레임 데이터가 없습니다.")
        return

    # 지정한 크기의 검은 화면 생성
    height, width = window_size[1], window_size[0]
    
    frame_index = 0
    while True:
        # 빈 검은 화면 생성 (BGR, 검정색)
        canvas = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 현재 프레임 데이터 선택 (순차적으로 표시)
        frame_data = frames_data[frame_index]
        
        # 각 종류의 랜드마크 오버레이 (색상은 임의로 지정)
        draw_landmarks(canvas, frame_data.get("pose_landmarks"), color=(0, 255, 0), radius=4)
        draw_landmarks(canvas, frame_data.get("face_landmarks"), color=(255, 0, 0), radius=4)
        draw_landmarks(canvas, frame_data.get("left_hand_landmarks"), color=(0, 0, 255), radius=4)
        draw_landmarks(canvas, frame_data.get("right_hand_landmarks"), color=(255, 255, 0), radius=4)
        
        # 프레임 번호 오버레이
        cv2.putText(canvas, f"Frame: {frame_index+1}/{total_frames}", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
        
        cv2.imshow("Landmark Check", canvas)
        key = cv2.waitKey(delay)
        if key & 0xFF == ord('q'):
            break

        frame_index += 1
        if frame_index >= total_frames:
            # 반복 재생 또는 종료: 여기서는 종료
            print("모든 프레임 표시 완료.")
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    # JSON 파일 경로를 명령줄 인자로 받을 수 있도록 함
    # if len(sys.argv) < 2:
    #     print("Usage: python landmark_check.py path/to/normalized_result.json")
    #     sys.exit(1)

    json_file = 'output/youtube_result/result_1742213016.json'
    display_landmarks_from_json(json_file)
