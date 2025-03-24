import cv2
import mediapipe as mp
import time
import os
import json
import asyncio

from utils.landmark_utils import landmark_list_to_dict, normalize_landmarks
from utils.logging_utils import logger
from models.request_models import LandmarkCreate
from crud.landmark import create_landmark
from db.session import SessionLocal

mp_holistic = mp.solutions.holistic

async def process_video(video_url: str):
    logger.info(f"비디오 처리 시작: {video_url}")

    cap = await asyncio.to_thread(cv2.VideoCapture, video_url)
    if not cap.isOpened():
        logger.error("비디오 스트림 열기 실패")
        return

    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        refine_face_landmarks=True
    )

    processed_frames = []
    frame_count = 0
    start_time = time.time()

    try:
        while True:
            ret, frame = await asyncio.to_thread(cap.read)
            if not ret:
                break

            frame_count += 1
            if frame_count % 1000 == 0:
                logger.info(f"{frame_count} 프레임 처리 중...")

            image_rgb = await asyncio.to_thread(cv2.cvtColor, frame, cv2.COLOR_BGR2RGB)
            results = await asyncio.to_thread(holistic.process, image_rgb)

            pose_lm = results.pose_landmarks.landmark if results.pose_landmarks else []
            face_lm = results.face_landmarks.landmark if results.face_landmarks else []
            left_lm = results.left_hand_landmarks.landmark if results.left_hand_landmarks else []
            right_lm = results.right_hand_landmarks.landmark if results.right_hand_landmarks else []

            nose_x, nose_y = 0.5, 0.5
            if face_lm:
                nose_x, nose_y = face_lm[1].x, face_lm[1].y
            elif pose_lm:
                nose_x, nose_y = pose_lm[0].x, pose_lm[0].y

            offset_x, offset_y = 0.5 - nose_x, 0.5 - nose_y
            all_lm = []
            
            for lm in [pose_lm, face_lm, left_lm, right_lm]:
                if lm:
                    all_lm.extend(lm)
                    
            if all_lm:
                normalize_landmarks(all_lm, offset_x, offset_y)

            frame_data = {
                "frame": frame_count,
                "pose_landmarks": landmark_list_to_dict(pose_lm) if pose_lm else None,
                "face_landmarks": landmark_list_to_dict(face_lm) if face_lm else None,
                "left_hand_landmarks": landmark_list_to_dict(left_lm) if left_lm else None,
                "right_hand_landmarks": landmark_list_to_dict(right_lm) if right_lm else None
            }
            processed_frames.append(frame_data)

            await asyncio.sleep(0)

    except Exception as e:
        logger.error(f"프레임 처리 중 오류 발생: {e}", exc_info=True)
    finally:
        cap.release()
        holistic.close()

    total_time = time.time() - start_time
    fps = frame_count / total_time if total_time > 0 else 0

    result = {
        "status": "processed",
        "total_frames_processed": frame_count,
        "total_processing_time_sec": total_time,
        "average_fps": fps,
        "data": processed_frames
    }

    # JSON 저장 (임시)
    output_dir = "output/youtube_result"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"result_{int(time.time())}.json")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, separators=(',', ':'))

        logger.info(f"결과 저장 완료: {output_file}")
    except Exception as e:
        logger.error(f"결과 저장 실패: {e}", exc_info=True)

    # 용량 확인인
    json_string = json.dumps(result, ensure_ascii=False)
    logger.info(f"✅ landmark JSON 크기: {len(json_string)} bytes ≈ {len(json_string)/1024/1024:.2f} MB")    

    # DB 저장
    db = SessionLocal() 
    try:
        landmark_data = LandmarkCreate(
            landmark=json.dumps(result, ensure_ascii=False),
            youtube_link=video_url
        )
        create_landmark(db, landmark=landmark_data)
        logger.info(f"[DB 저장 완료] video_url: {video_url}")
    except Exception as e:
        logger.error(f"[DB 저장 실패] {e}", exc_info=True)
    finally:
        db.close()
