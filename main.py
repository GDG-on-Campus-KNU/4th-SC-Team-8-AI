from fastapi import FastAPI, HTTPException, WebSocket, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from utils.youtube_utils import extract_youtube_stream_url
from utils.process_video_utils import process_video
from utils.youtube_subtitle_utils import get_subtitle_text
from models.request_models import YouTubeRequest, SubtitleRequest
from models.response_models import ProcessResponse, SubtitleResponse, TestResponse
from utils.similarity_compare_utils import fetch_reference_landmark, fetch_user_landmark, compare_landmark, score_to_label

from sqlalchemy.ext.asyncio import AsyncSession
from db.session import get_db, AsyncSessionLocal
from crud.game import get_game_by_url

import json
import uvicorn
import asyncio
from utils.logging_utils import logger

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
async def process_youtube(req: YouTubeRequest, db: AsyncSession = Depends(get_db)):
    try:
        existing_game = await get_game_by_url(db, youtube_link=req.url)
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
async def landmark_socket(websocket: WebSocket, video_url: str = Query(...)):
    await websocket.accept()

    try:
        scores = []
        labels = []
        label_count = {
            "perfect": 0,
            "great": 0,
            "good": 0,
            "bad": 0
        }

        async with AsyncSessionLocal() as db:
            game = await get_game_by_url(db, youtube_link=video_url)
            landmark = game.landmark
            reference_landmark = json.loads(landmark)
                
        while True:
            data = await websocket.receive_json()
    
            start_ms = data["start_ms"]
            end_ms = data["end_ms"]
            user_landmark = data["data"]
            is_last_sentence = data.get("is_last_sentence", False)

            reference = fetch_reference_landmark(start_ms, end_ms, reference_landmark)
            user = fetch_user_landmark(user_landmark)
            score = compare_landmark(reference, user)

            print("reference", len(reference))
            print("user", len(user))
            
            label = score_to_label(score)
            scores.append(score)
            labels.append(label)

            if label in label_count:
                label_count[label] += 1

            await websocket.send_json({
                "sentence_score": score,
                "sentence_label": label,
                "label_count": label_count,
                "index": len(scores) - 1
            })
            
            if is_last_sentence:
                await websocket.send_json({
                    "final_scores": label_count,
                    "last": True
                })
                break

    except Exception as e:
        print("WebSocket error:", e)
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass 
        print("WebSocket 정상 종료")


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
    uvicorn.run(app, host="0.0.0.0", port=8000)