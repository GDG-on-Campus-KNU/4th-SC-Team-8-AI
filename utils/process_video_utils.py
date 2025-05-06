from __future__ import annotations
import os, json, time, cv2, traceback
from pathlib import Path
from typing import List, Dict
import mediapipe as mp

from utils.logging_utils import logger
from utils.common import extract_yt_id
from utils.landmark_utils import (
    landmark_list_to_dict, normalize_landmarks
)
from models.request_models import GameCreate
from crud.game import create_game
from db.session import SessionLocal

OUT_DIR = Path("output/youtube_result")
OUT_DIR.mkdir(parents=True, exist_ok=True)

mp_holistic = mp.solutions.holistic.Holistic(
    static_image_mode=False,
    model_complexity=1,
    enable_segmentation=False,
    refine_face_landmarks=False,
)

def process_video(request_url: str, video_url: str) -> None:
    """동기 함수 — asyncio.to_thread 로 실행"""
    request_url = str(request_url)
    youtube_id  = extract_yt_id(request_url) or "unknown"
    ts_start    = int(time.time())
    json_path   = OUT_DIR / f"{youtube_id}_{ts_start}.json"
    logger.info("[비디오 처리 시작] %s", youtube_id)

    cap = cv2.VideoCapture(video_url)
    if not cap.isOpened():
        logger.error("[VideoCapture 실패] %s", video_url)
        return

    fps          = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    processed_frames: List[Dict] = []

    frame_ms  = 1_000 / fps
    frame_idx = 0
    last_pct  = -1
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            ts_ms = int(frame_idx * frame_ms)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            res = mp_holistic.process(rgb)

            left_lm   = res.left_hand_landmarks
            right_lm  = res.right_hand_landmarks
            has_any = any([left_lm, right_lm])

            if has_any:
                frame_data = {
                    "frame": frame_idx,
                    "timestamp_ms": ts_ms,
                    "left_hand_landmarks": landmark_list_to_dict(left_lm) if left_lm else None,
                    "right_hand_landmarks": landmark_list_to_dict(right_lm) if right_lm else None
                }
                processed_frames.append(frame_data)

            frame_idx += 1

            if total_frames:
                pct = int(frame_idx / total_frames * 100)
                if pct != last_pct and pct % 2 == 0:
                    print(f"\r[Holistic] {youtube_id}  {pct:3d}% 진행 중...", end="")
                    last_pct = pct

    except Exception:
        logger.error("[Holistic 처리 예외]\n%s", traceback.format_exc())
    finally:
        cap.release()
        if total_frames:
            pct = int(frame_idx / total_frames * 100)
            if pct != last_pct and pct % 2 == 0:
                logger.info("[Holistic] %s %3d%%", youtube_id, pct)

    result = {
        "youtube_link": request_url,
        "youtube_id": youtube_id,
        "fps": fps,
        "data": processed_frames,
    }

    # JSON 저장
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            separators=(",", ":")  # 공백 제거
        )

    logger.info("[결과 저장 완료] %s (프레임 %d)", json_path, len(processed_frames))

    # DB 저장
    db = SessionLocal()
    try:
        game_data = GameCreate(
            landmark=json.dumps(result, ensure_ascii=False, separators=(",", ":")),
            youtube_link=request_url
        )
        saved = create_game(db, game=game_data)
        if saved and saved.youtube_link == request_url:
            logger.info("[DB 저장 완료] id=%s, youtube_link=%s", saved.id, saved.youtube_link)
        else:
            logger.warning("[DB 저장 확인 실패] 반환값이 예상과 다름")
    except Exception as e:
        db.rollback()
        logger.error("[DB 저장 실패] %s", traceback.format_exc())
    finally:
        db.close()
