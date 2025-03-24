import cv2
import mediapipe as mp
import time
import os
import json
import asyncio
from utils.landmark_utils import landmark_list_to_dict, normalize_landmarks
from utils.logging_utils import logger  # 로그 설정 가져오기

mp_holistic = mp.solutions.holistic

async def process_video(video_url: str):
    """
    YouTube 비디오를 처리하여 랜드마크 정보를 JSON으로 저장한다.
    """
    logger.info(f"백그라운드 작업 시작: {video_url}")

    cap = await asyncio.to_thread(cv2.VideoCapture, video_url)
    if not cap.isOpened():
        logger.error("Error: 비디오 스트림을 열 수 없음")
        return

    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        refine_face_landmarks=True
    )

    processed_frames = []
    overall_frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = await asyncio.to_thread(cap.read)
            if not ret:
                logger.warning("비디오 끝 또는 프레임 읽기 에러 발생")
                break

            overall_frame_count += 1
            LOG_INTERVAL = 1000  # 로그 출력 간격 (1000 프레임)

            if overall_frame_count % LOG_INTERVAL == 0:
                logger.info(f"처리 중... 현재 프레임 번호: {overall_frame_count}")

            image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = await asyncio.to_thread(holistic.process, image_rgb)

            pose_lm = results.pose_landmarks.landmark if results.pose_landmarks else []
            face_lm = results.face_landmarks.landmark if results.face_landmarks else []
            left_lm = results.left_hand_landmarks.landmark if results.left_hand_landmarks else []
            right_lm = results.right_hand_landmarks.landmark if results.right_hand_landmarks else []

            nose_x, nose_y = 0.0, 0.0
            if face_lm:
                nose_x, nose_y = face_lm[1].x, face_lm[1].y # face 기준 코 좌표 : 1
            elif pose_lm:
                nose_x, nose_y = pose_lm[0].x, pose_lm[0].y # pose 기준 코 좌표 : 0
            
            offset_x, offset_y = 0.5 - nose_x, 0.5 - nose_y

            all_lm = []
            for lm in [pose_lm, face_lm, left_lm, right_lm]:
                if lm:
                    all_lm.extend(lm)

            if all_lm:
                normalize_landmarks(all_lm, offset_x, offset_y)

            frame_data = {
                "frame": overall_frame_count,
                "pose_landmarks": landmark_list_to_dict(pose_lm) if pose_lm else None,
                "face_landmarks": landmark_list_to_dict(face_lm) if face_lm else None,
                "left_hand_landmarks": landmark_list_to_dict(left_lm) if left_lm else None,
                "right_hand_landmarks": landmark_list_to_dict(right_lm) if right_lm else None
            }

            processed_frames.append(frame_data)

            await asyncio.sleep(0)

    except Exception as e:
        logger.error(f"예외 발생: {str(e)}", exc_info=True)

    finally:
        cap.release()
        holistic.close()

    total_time = time.time() - start_time
    avg_fps = overall_frame_count / total_time if total_time > 0 else 0

    logger.info(f"처리 완료: 총 {overall_frame_count} 프레임, 실행 시간: {total_time:.2f}초, FPS: {avg_fps:.2f}")

    result = {
        "status": "processed",
        "total_frames_processed": overall_frame_count,
        "total_processing_time_sec": total_time,
        "average_fps": avg_fps,
        "data": processed_frames
    }

    output_dir = "output/youtube_result"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"result_{int(time.time())}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    logger.info(f"결과 JSON 파일 저장 완료: {output_file}")
