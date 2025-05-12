import cv2
import mediapipe as mp
import time
import json
import asyncio

from utils.logging_utils import logger
from utils.email_utils import send_mail_notification
from models.request_models import GameCreate
from crud.game import create_game
from db.session import AsyncSessionLocal

mp_holistic = mp.solutions.holistic

def landmark_list_to_dict(landmarks):
    """랜드마크를 딕셔너리 리스트로 변환"""
    if not landmarks:
        return None
    return [{"x": lm.x, "y": lm.y, "z": lm.z, "visibility": getattr(lm, 'visibility', 1.0)} for lm in landmarks]

async def process_video(request_url: str, video_url: str):
    prefix = f"[{request_url}]"
    logger.info(f"{prefix} 비디오 처리 시작")

    cap = await asyncio.to_thread(cv2.VideoCapture, video_url)
    if not cap.isOpened():
        logger.error(f"{prefix} 비디오 스트림 열기 실패")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        logger.error(f"{prefix} FPS 정보를 가져오지 못했습니다. timestamp 계산 불가 → 처리 중단")
        return 

    logger.info(f"{prefix} FPS: {fps:.3f}")

    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        enable_segmentation=False,
        refine_face_landmarks=True
    )

    processed_frames = []
    frame_count = 0
    start_time = time.time()

    error_during_processing = False  # 처리 중 에러 플래그

    try:
        while True:
            ret, frame = await asyncio.to_thread(cap.read)
            if not ret:
                break

            frame_count += 1
            if frame_count % 1000 == 0:
                logger.info(f"{prefix} {frame_count} 프레임 처리 중...")

            image_rgb = await asyncio.to_thread(cv2.cvtColor, frame, cv2.COLOR_BGR2RGB)
            results = await asyncio.to_thread(holistic.process, image_rgb)

            left_lm = results.left_hand_landmarks.landmark if results.left_hand_landmarks else []
            right_lm = results.right_hand_landmarks.landmark if results.right_hand_landmarks else []

            # 정규화를 제거하고 원본 랜드마크 그대로 저장
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
        error_during_processing = True
        logger.error(f"{prefix} 프레임 처리 중 오류 발생: {e}", exc_info=True)
    finally:
        cap.release()
        holistic.close()

    if error_during_processing or not processed_frames:
        logger.warning(f"{prefix} [처리 실패] 프레임 처리 중 오류로 인해 DB 저장 및 이메일 전송 생략")
        await send_mail_notification(request_url, status="FAIL")  # 실패 시 FAIL 전송
        return

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
                logger.info(f"{prefix} [DB 저장 완료] id={saved_game.id}, video_url={saved_game.youtube_link}")
            else:
                logger.warning(f"{prefix} [DB 저장 확인 실패] 반환값이 예상과 다름")
        except Exception as e:
            await db.rollback()
            logger.error(f"{prefix} [DB 저장 실패] {e}", exc_info=True)

    await send_mail_notification(request_url, status="SUCCESS")