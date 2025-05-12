import cv2
import mediapipe as mp
import time
import os
import json
import asyncio

from utils.landmark_utils import landmark_list_to_dict, normalize_landmarks
from utils.logging_utils import logger
from models.request_models import GameCreate
from crud.game import create_game
from db.session import AsyncSessionLocal  # 비동기 세션 사용

mp_holistic = mp.solutions.holistic

async def process_video(request_url: str, video_url: str):
    logger.info(f"비디오 처리 시작: {request_url}")

    cap = await asyncio.to_thread(cv2.VideoCapture, video_url)
    if not cap.isOpened():
        logger.error("비디오 스트림 열기 실패")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        logger.error("FPS 정보를 가져오지 못했습니다. timestamp 계산 불가 → 처리 중단")
        return 

    logger.info(f'FPS: {fps:.3f}')

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

            # pose_lm = results.pose_landmarks.landmark if results.pose_landmarks else []
            # face_lm = results.face_landmarks.landmark if results.face_landmarks else []
            left_lm = results.left_hand_landmarks.landmark if results.left_hand_landmarks else []
            right_lm = results.right_hand_landmarks.landmark if results.right_hand_landmarks else []

            nose_x, nose_y = 0.5, 0.5
            # if face_lm:
            #     nose_x, nose_y = face_lm[1].x, face_lm[1].y
            # elif pose_lm:
            #     nose_x, nose_y = pose_lm[0].x, pose_lm[0].y

            offset_x, offset_y = 0.5 - nose_x, 0.5 - nose_y
            all_lm = []
            for lm in [left_lm, right_lm]:
                if lm:
                    all_lm.extend(lm)
            if all_lm:
                normalize_landmarks(all_lm, offset_x, offset_y)

            timestamp_ms = int(frame_count / fps * 1000)

            frame_data = {
                "frame": frame_count,
                "timestamp_ms": timestamp_ms,
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
    avg_fps = frame_count / total_time if total_time > 0 else 0

    result = {
        "status": "processed",
        "total_frames_processed": frame_count,
        "total_processing_time_sec": total_time,
        "average_fps": avg_fps,
        "fps_used": fps,
        "data": processed_frames
    }
    
    async with AsyncSessionLocal() as db:
        try:
            game_data = GameCreate(
                landmark=json.dumps(result, ensure_ascii=False),
                youtube_link=request_url
            )
            saved_game = await create_game(db, game=game_data)

            if saved_game and saved_game.youtube_link == request_url:
                logger.info(f"[DB 저장 완료 ] id={saved_game.id}, video_url={saved_game.youtube_link}")
            else:
                logger.warning(f"[DB 저장 확인 실패 ] 반환값이 예상과 다름")
        except Exception as e:
            await db.rollback()
            logger.error(f"[DB 저장 실패] {e}", exc_info=True)
            