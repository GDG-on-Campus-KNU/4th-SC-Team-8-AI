from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from utils.youtube_utils import extract_youtube_stream_url
from utils.process_video_utils import process_video
from utils.youtube_subtitle_utils import get_subtitle_text
from models.request_models import YouTubeRequest, SubtitleRequest
from models.response_models import ProcessResponse, SubtitleResponse, TestResponse
from utils.similarity_compare_utils import fetch_landmark, compare_landmark

from fastapi import Depends
from sqlalchemy.orm import Session
from db.session import get_db, SessionLocal
from crud.game import get_game_by_url

import uvicorn
import asyncio

app = FastAPI(title="YouTube Landmark Processor API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/test", response_model=TestResponse)
async def test_endpoint():
    return {"status": "success", "message": "API is reachable"}

@app.post("/process_youtube", response_model=ProcessResponse)
async def process_youtube(req: YouTubeRequest, db: Session = Depends(get_db)):
    try:
        existing_game = get_game_by_url(db, youtube_link=req.url)
        if existing_game:
            return {
                "status": "already processed",
                "video_url": req.url
            }

        video_url = extract_youtube_stream_url(req.url)

        asyncio.create_task(process_video(req.url, video_url))

        return {
            "status": "processing started",
            "video_url": video_url
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/landmark")
async def landmark_socket(websocket: WebSocket):
    await websocket.accept()
    scores = []
    video_url = None
    landmark = None
    db : Session = SessionLocal()
    try:
        while True:
            data = await websocket.receive_json()

            if not video_url:
                video_url = data["video_url"]
                game = get_game_by_url(db, youtube_link=video_url)
                landmark = game.landmark
            
            start_ms = data["start_ms"]
            end_ms = data["end_ms"]
            user_landmark = data["user_landmark"]
            is_last_sentence = data.get("is_last_sentence", False)

            reference = fetch_landmark(start_ms, end_ms)
            user_processed = [x["landmark"] for x in user_landmark]
            score = compare_landmark(reference, user_processed)

            scores.append(score)

            # 실시간 개별 점수 전송
            await websocket.send_json({
                "sentence_score": score,
                "index": len(scores) - 1
            })

            # 마지막 문장이면 전체 점수도 함께 전송 후 종료료
            if is_last_sentence:
                await websocket.send_json({
                    "final_scores": scores
                })
                break

    except Exception as e:
        await websocket.close()
        db.close()
        print("WebSocket error:", e)
    finally:
        db.close()
        await websocket.close()
        print("Websocket 정상 종료")
    

@app.post("/get_subtitle", response_model=SubtitleResponse)
async def get_subtitle(req: SubtitleRequest):
    try:
        subtitle_text = get_subtitle_text(req.url, req.lang)
        if not subtitle_text:
            raise HTTPException(status_code=404, detail=f"'{req.lang}' 자막이 없습니다.")
        return {"status": "success", "subtitle": subtitle_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
