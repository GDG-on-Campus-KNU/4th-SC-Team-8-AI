# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from utils.youtube_utils import extract_youtube_stream_url
# # from utils.process_video_utils import process_video
# # from utils.youtube_subtitle_utils import get_subtitle_text
# # from models.request_models import YouTubeRequest, SubtitleRequest
# # from models.response_models import ProcessResponse, SubtitleResponse, TestResponse

# # from fastapi import Depends
# # from sqlalchemy.orm import Session
# # from db.session import get_db
# # from crud.game import get_game_by_url

# # import uvicorn
# # import asyncio

# # app = FastAPI(title="YouTube Landmark Processor API")

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],
# #     allow_methods=["*"],
# #     allow_headers=["*"]
# # )

    
# # @app.get("/test", response_model=TestResponse)
# # async def test_endpoint():
# #     return {"status": "success", "message": "API is reachable"}

# # @app.post("/process_youtube", response_model=ProcessResponse)
# # async def process_youtube(req: YouTubeRequest, db: Session = Depends(get_db)):
# #     try:
# #         existing_game = get_game_by_url(db, youtube_link=req.url)
# #         if existing_game:
# #             return {
# #                 "status": "already processed",
# #                 "video_url": req.url
# #             }

# #         video_url = extract_youtube_stream_url(req.url)

# #         asyncio.create_task(process_video(req.url, video_url))

# #         return {
# #             "status": "processing started",
# #             "video_url": video_url
# #         }

# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))

# # @app.post("/get_subtitle", response_model=SubtitleResponse)
# # async def get_subtitle(req: SubtitleRequest):
# #     try:
# #         subtitle_text = get_subtitle_text(req.url, req.lang)
# #         if not subtitle_text:
# #             raise HTTPException(status_code=404, detail=f"'{req.lang}' 자막이 없습니다.")
# #         return {"status": "success", "subtitle": subtitle_text}
# #     except Exception as e:
# #         raise HTTPException(status_code=500, detail=str(e))

# # if __name__ == "__main__":
# #     uvicorn.run(app, host="0.0.0.0", port=5000)

# import os
# import re
# import uuid
# import asyncio
# import shutil
# from tempfile import mkdtemp
# from typing import List

# from fastapi import (
#     FastAPI,
#     HTTPException,
#     Depends,
#     UploadFile,
#     File,
#     Form,
# )
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles

# from models.request_models import (
#     YouTubeRequest,
#     SubtitleRequest,
#     EvaluateCaptionRequest,
# )
# from models.response_models import (
#     ProcessResponse,
#     SubtitleResponse,
#     TestResponse,
#     EvaluateResponse,
# )
# from utils.youtube_utils import extract_youtube_stream_url
# from utils.youtube_subtitle_utils import get_subtitle_with_timing
# from utils.process_video_utils import process_video
# from utils.similarity_utils import (
#     build_sequence,
#     extract_landmark_sequence_from_video,
#     similarity,
#     rating as rating_from_dist,
# )
# from crud.game import (
#     get_game_by_url,
#     get_game_by_video_id,
# )
# from db.session import get_db
# from utils.logging_utils import logger

# app = FastAPI(title="Sign-Book Demo API")

# # ---------------------- CORS ----------------------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ------------------ 정적 파일 ----------------------
# app.mount(
#     "/static",
#     StaticFiles(directory="output", html=False),
#     name="static",
# )

# # ------------------- 헬퍼 -------------------------
# _YT_ID_RE = re.compile(r"(?<=v=)[\w-]{11}|(?<=youtu\.be/)[\w-]{11}")


# def _extract_youtube_id(url: str) -> str:
#     m = _YT_ID_RE.search(url)
#     return m.group(0) if m else ""


# # ------------------- 엔드포인트 --------------------
# @app.get("/test", response_model=TestResponse)
# async def test_api():
#     return {"status": "success", "message": "API is reachable"}


# @app.post("/process_youtube", response_model=ProcessResponse)
# async def process_youtube(req: YouTubeRequest, db=Depends(get_db)):
#     if get_game_by_url(db, youtube_link=req.url):
#         return {"status": "already processed", "video_url": req.url}

#     try:
#         video_url = extract_youtube_stream_url(req.url)
#     except Exception as e:
#         logger.error("[Stream URL 추출 실패]", exc_info=True)
#         raise HTTPException(status_code=500, detail=str(e))

#     asyncio.create_task(process_video(req.url, video_url))
#     return {"status": "processing started", "video_url": video_url}


# @app.post("/get_subtitle", response_model=SubtitleResponse)
# async def get_subtitle(req: SubtitleRequest):
#     captions, file_path = get_subtitle_with_timing(req.url, req.lang)
#     if captions is None:
#         raise HTTPException(status_code=404, detail=f"{req.lang} 자막이 없습니다.")

#     # /static 경로 계산
#     rel_path = os.path.relpath(file_path, "output").replace(os.sep, "/")
#     static_url = f"/static/{rel_path}"

#     return {
#         "status": "success",
#         "youtube_id": _extract_youtube_id(req.url),
#         "captions": captions,
#         "file_path": file_path,
#         "static_url": static_url,
#     }


# @app.post("/evaluate_caption", response_model=EvaluateResponse)

# async def evaluate_caption(
#     youtube_id: str = Form(...),
#     caption_start: float = Form(...),
#     caption_dur: float = Form(...),
#     video: UploadFile = File(...),
#     db=Depends(get_db),
# ):
#     """캡션 구간(초) 기준 유사도 평가"""
#     if not game or not game.landmark or game.landmark.strip() == "":
#         raise HTTPException(status_code=404, detail="랜드마크 데이터가 없습니다.")
#     # 1) 유튜브 랜드마크 JSON 로드
#     game = get_game_by_video_id(db, youtube_id)
#     if game is None:
#         raise HTTPException(status_code=404, detail="원본 랜드마크가 없습니다.")

#     try:
#         from json import loads

#         yt_data = loads(game.landmark)
#     except Exception as e:
#         logger.error("[게임 JSON 파싱 실패]", exc_info=True)
#         raise HTTPException(status_code=500, detail="DB JSON 오류")

#     frames: List[dict] = yt_data.get("data", [])
#     seq_ref = build_sequence(
#         frames,
#         start_ms=int(caption_start * 1000),
#         end_ms=int((caption_start + caption_dur) * 1000),
#     )
#     if not seq_ref:
#         raise HTTPException(status_code=400, detail="참조 시퀀스가 없습니다.")

#     # 2) 업로드 영상 임시 저장
#     tmp_dir = mkdtemp(prefix="webcam_")
#     video_path = os.path.join(tmp_dir, f"{uuid.uuid4()}.webm")
#     with open(video_path, "wb") as f:
#         shutil.copyfileobj(video.file, f)

#     # 3) 웹캠 랜드마크 시퀀스 추출
#     seq_test = extract_landmark_sequence_from_video(video_path)

#     shutil.rmtree(tmp_dir, ignore_errors=True)

#     if not seq_test:
#         return {
#             "score": 9999.0,
#             "rating": "no_data",
#         }

#     # 4) DTW 거리 & 등급
#     dist = similarity(seq_ref, seq_test)
#     score_rating = rating_from_dist(dist)
#     return {
#         "score": dist,
#         "rating": score_rating,
#     }
###########################################################
####################only for LOCAL#########################
import os, asyncio, uuid, shutil, glob, json
from functools import partial
from fastapi import (
    FastAPI, HTTPException, UploadFile, File, Form
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models.request_models import YouTubeRequest, SubtitleRequest
from models.response_models import (
    ProcessResponse, SubtitleResponse, TestResponse, EvaluateResponse
)
from utils.youtube_utils import extract_youtube_stream_url
from utils.youtube_subtitle_utils import get_subtitle_with_timing
from utils.process_video_utils import process_video
from utils.similarity_utils import (
    build_sequence, extract_landmark_sequence_from_video,
    similarity, rating as rating_from_dist
)
from utils.file_lookup_utils import (
    find_latest_json, is_ready
)
from utils.logging_utils import logger
from utils.common import extract_yt_id   # ★ ID 추출 유틸

from datetime import datetime, timedelta
from utils.file_lookup_utils import find_latest_json, is_ready

PROCESSING_GRACE = timedelta(minutes=50)   # 최근 5분 이내면 '진행 중'으로 간주
app = FastAPI(title="Sign-Book Demo (No-DB, Pre-process)")

# ----------- CORS -----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- 정적 -----------
app.mount("/static", StaticFiles(directory="output"), name="static")

# ----------- 기본 ----------
@app.get("/test", response_model=TestResponse)
async def test_api():
    return {"status": "success", "message": "API is reachable"}

# ----------- 1. 준비(사전 추출) ----------
@app.post("/prepare_youtube", response_model=ProcessResponse)
async def prepare_youtube(req: YouTubeRequest):
    youtube_id = extract_yt_id(str(req.url))
    if not youtube_id:
        raise HTTPException(400, "유효한 YouTube URL 아님")

    # ① 이미 랜드마크 완성
    if is_ready(youtube_id):
        return {"status": "ready", "video_url": str(req.url)}

    # ② JSON 은 있으나 data 가 비어 있고, 생성 시각이 매우 최근
    json_path = find_latest_json(youtube_id)
    if json_path:
        mtime = datetime.fromtimestamp(os.path.getmtime(json_path))
        if datetime.now() - mtime < PROCESSING_GRACE:
            return {"status": "processing", "video_url": str(req.url)}
        # → 오래된 빈 파일이면 실패로 간주하고 새로 추출

    # ③ 새 추출 시작
    try:
        video_url = await asyncio.to_thread(extract_youtube_stream_url, str(req.url))
    except Exception as e:
        logger.error("[스트림 URL 추출 실패]", exc_info=True)
        raise HTTPException(500, str(e))

    # 동기 함수 → 백그라운드 스레드 실행
    asyncio.create_task(
        asyncio.to_thread(process_video, str(req.url), video_url)
    )
    return {"status": "processing", "video_url": str(req.url)}
# ----------- 2. 준비 상태 확인 ----------
@app.get("/check_ready")
async def check_ready(youtube_id: str):
    return {"ready": is_ready(youtube_id)}

# ----------- 3. 자막 ----------
@app.post("/get_subtitle", response_model=SubtitleResponse)
async def get_subtitle(req: SubtitleRequest):
    captions, file_path = get_subtitle_with_timing(str(req.url), req.lang)
    if captions is None:
        raise HTTPException(404, f"{req.lang} 자막이 없습니다.")

    youtube_id = extract_yt_id(str(req.url))  
    rel_path   = os.path.relpath(file_path, "output").replace(os.sep, "/")
    return {"status":"success", "youtube_id":youtube_id,
            "captions":captions,
            "file_path":file_path,
            "static_url":f"/static/{rel_path}"}

# ----------- 4. 캡션 평가 ----------
@app.post("/evaluate_caption", response_model=EvaluateResponse)
async def evaluate_caption(
    youtube_id: str = Form(...),
    caption_start: float = Form(...),
    caption_dur: float = Form(...),
    video: UploadFile = File(...),
):
    json_path = find_latest_json(youtube_id)
    if not json_path:
        raise HTTPException(404, "랜드마크 JSON 준비되지 않음")

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)
    seq_ref = build_sequence(
        data.get("data", []),
        start_ms=int(caption_start*1000),
        end_ms=int((caption_start+caption_dur)*1000),
    )
    if not seq_ref:
        raise HTTPException(400, "참조 시퀀스 없음")

    tmp_dir = os.path.join("tmp", str(uuid.uuid4()))
    os.makedirs(tmp_dir, exist_ok=True)
    vid_path = os.path.join(tmp_dir, "cam.webm")
    with open(vid_path, "wb") as fDst:
        shutil.copyfileobj(video.file, fDst)

    seq_test = extract_landmark_sequence_from_video(vid_path)
    shutil.rmtree(tmp_dir, ignore_errors=True)

    if not seq_test:
        return {"score": 9999.0, "rating": "no_data"}

    dist = similarity(seq_ref, seq_test)
    return {"score": dist, "rating": rating_from_dist(dist)}
