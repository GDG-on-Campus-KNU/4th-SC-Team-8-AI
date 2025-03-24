from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from utils.youtube_utils import extract_youtube_stream_url
from utils.process_video_utils import process_video
from utils.youtube_subtitle import get_subtitle_text
from models.request_models import YouTubeRequest, SubtitleRequest
from models.response_models import ProcessResponse, SubtitleResponse, TestResponse

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
async def process_youtube(req: YouTubeRequest):
    try:
        video_url = extract_youtube_stream_url(req.url)
        asyncio.create_task(process_video(video_url))
        return {"status": "processing started", "video_url": video_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
