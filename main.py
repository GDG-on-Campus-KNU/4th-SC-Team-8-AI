# ###########################################################
# ####################only for LOCAL#########################
# import os, asyncio, uuid, shutil, glob, json
# from functools import partial
# from fastapi import (
#     FastAPI, HTTPException, UploadFile, File, Form
# )
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles

# from models.request_models import YouTubeRequest, SubtitleRequest
# from models.response_models import (
#     ProcessResponse, SubtitleResponse, TestResponse, EvaluateResponse
# )
# from utils.youtube_utils import extract_youtube_stream_url
# from utils.youtube_subtitle_utils import get_subtitle_with_timing
# from utils.process_video_utils import process_video
# from utils.similarity_utils import (
#     build_sequence, extract_landmark_sequence_from_video,
#     similarity, rating as rating_from_dist
# )
# from utils.file_lookup_utils import (
#     find_latest_json, is_ready
# )
# from utils.logging_utils import logger
# from utils.common import extract_yt_id   # ★ ID 추출 유틸

# from datetime import datetime, timedelta
# from utils.file_lookup_utils import find_latest_json, is_ready

# PROCESSING_GRACE = timedelta(minutes=50)   # 최근 5분 이내면 '진행 중'으로 간주
# app = FastAPI(title="Sign-Book Demo (No-DB, Pre-process)")

# # ----------- CORS -----------
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ----------- 정적 -----------
# app.mount("/static", StaticFiles(directory="output"), name="static")

# # ----------- 기본 ----------
# @app.get("/test", response_model=TestResponse)
# async def test_api():
#     return {"status": "success", "message": "API is reachable"}

# # ----------- 1. 준비(사전 추출) ----------
# @app.post("/prepare_youtube", response_model=ProcessResponse)
# async def prepare_youtube(req: YouTubeRequest):
#     youtube_id = extract_yt_id(str(req.url))
#     if not youtube_id:
#         raise HTTPException(400, "유효한 YouTube URL 아님")

#     # ① 이미 랜드마크 완성
#     if is_ready(youtube_id):
#         return {"status": "ready", "video_url": str(req.url)}

#     # ② JSON 은 있으나 data 가 비어 있고, 생성 시각이 매우 최근
#     json_path = find_latest_json(youtube_id)
#     if json_path:
#         mtime = datetime.fromtimestamp(os.path.getmtime(json_path))
#         if datetime.now() - mtime < PROCESSING_GRACE:
#             return {"status": "processing", "video_url": str(req.url)}
#         # → 오래된 빈 파일이면 실패로 간주하고 새로 추출

#     # ③ 새 추출 시작
#     try:
#         video_url = await asyncio.to_thread(extract_youtube_stream_url, str(req.url))
#     except Exception as e:
#         logger.error("[스트림 URL 추출 실패]", exc_info=True)
#         raise HTTPException(500, str(e))

#     # 동기 함수 → 백그라운드 스레드 실행
#     asyncio.create_task(
#         asyncio.to_thread(process_video, str(req.url), video_url)
#     )
#     return {"status": "processing", "video_url": str(req.url)}
# # ----------- 2. 준비 상태 확인 ----------
# @app.get("/check_ready")
# async def check_ready(youtube_id: str):
#     return {"ready": is_ready(youtube_id)}

# # ----------- 3. 자막 ----------
# @app.post("/get_subtitle", response_model=SubtitleResponse)
# async def get_subtitle(req: SubtitleRequest):
#     captions, file_path = get_subtitle_with_timing(str(req.url), req.lang)
#     if captions is None:
#         raise HTTPException(404, f"{req.lang} 자막이 없습니다.")

#     youtube_id = extract_yt_id(str(req.url))  
#     rel_path   = os.path.relpath(file_path, "output").replace(os.sep, "/")
#     return {"status":"success", "youtube_id":youtube_id,
#             "captions":captions,
#             "file_path":file_path,
#             "static_url":f"/static/{rel_path}"}

# # ----------- 4. 캡션 평가 ----------
# @app.post("/evaluate_caption", response_model=EvaluateResponse)
# async def evaluate_caption(
#     youtube_id: str = Form(...),
#     caption_start: float = Form(...),
#     caption_dur: float = Form(...),
#     video: UploadFile = File(...),
# ):
#     json_path = find_latest_json(youtube_id)
#     if not json_path:
#         raise HTTPException(404, "랜드마크 JSON 준비되지 않음")

#     with open(json_path, encoding="utf-8") as f:
#         data = json.load(f)
#     seq_ref = build_sequence(
#         data.get("data", []),
#         start_ms=int(caption_start*1000),
#         end_ms=int((caption_start+caption_dur)*1000),
#     )
#     if not seq_ref:
#         raise HTTPException(400, "참조 시퀀스 없음")

#     tmp_dir = os.path.join("tmp", str(uuid.uuid4()))
#     os.makedirs(tmp_dir, exist_ok=True)
#     vid_path = os.path.join(tmp_dir, "cam.webm")
#     with open(vid_path, "wb") as fDst:
#         shutil.copyfileobj(video.file, fDst)

#     seq_test = extract_landmark_sequence_from_video(vid_path)
#     shutil.rmtree(tmp_dir, ignore_errors=True)

#     if not seq_test:
#         return {"score": 9999.0, "rating": "no_data"}

#     dist = similarity(seq_ref, seq_test)
#     return {"score": dist, "rating": rating_from_dist(dist)}






###########################################################
####################only for LOCAL#########################
###########################################################
####################only for LOCAL#########################
import os, asyncio, uuid, shutil, glob, json
from functools import partial
from fastapi import (
    FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect
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
from utils.file_lookup_utils import is_ready
from utils.logging_utils import logger
from utils.common import extract_yt_id   # ★ ID 추출 유틸

from crud.game import get_latest_game_by_link
from db.session import SessionLocal

from datetime import datetime, timedelta

PROCESSING_GRACE = timedelta(minutes=50)   # 최근 50분 이내면 '진행 중'으로 간주
app = FastAPI(title="Sign-Book Demo (DB-backed)")

# ----------- CORS -----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------- 정적 -----------
app.mount("/static", StaticFiles(directory="output"), name="static")

# ----------- WebSocket Manager -----------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# ----------- WebSocket Endpoint -----------
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # 클라이언트로부터 받는 메시지 처리 (선택 사항)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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

    if is_ready(youtube_id):
        return {"status": "ready", "video_url": str(req.url)}

    # JSON old check omitted for brevity...

    video_url = await asyncio.to_thread(extract_youtube_stream_url, str(req.url))
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
    rel_path = os.path.relpath(file_path, "output").replace(os.sep, "/")
    return {
        "status": "success",
        "youtube_id": youtube_id,
        "captions": captions,
        "file_path": file_path,
        "static_url": f"/static/{rel_path}"
    }

# ----------- 4. 캡션 평가 (DB에서 JSON 로드) ----------
@app.post("/evaluate_caption", response_model=EvaluateResponse)
async def evaluate_caption(
    youtube_id: str = Form(...),
    caption_start: float = Form(...),
    caption_dur: float = Form(...),
    video: UploadFile = File(...),
):
    # DB에서 마지막 저장된 game 레코드 가져오기
    db = SessionLocal()
    try:
        game = get_latest_game_by_link(db, youtube_id)
    finally:
        db.close()

    if not game or not game.landmark:
        raise HTTPException(404, "랜드마크 데이터가 DB에 없습니다.")

    data_record = json.loads(game.landmark)
    seq_ref = build_sequence(
        data_record.get("data", []),
        start_ms=int(caption_start * 1000),
        end_ms=int((caption_start + caption_dur) * 1000),
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
        dist = 9999.0
        rating = "no_data"
    else:
        dist = similarity(seq_ref, seq_test)
        rating = rating_from_dist(dist)

    await manager.broadcast(json.dumps({"score": dist, "rating": rating}))
    return {"score": dist, "rating": rating}
