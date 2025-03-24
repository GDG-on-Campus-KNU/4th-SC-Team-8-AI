from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from utils.youtube_utils import extract_youtube_stream_url
from utils.process_video_utils import process_video
from models.request_models import YouTubeRequest
from utils.logging_utils import logger 
from pydantic import BaseModel
import uvicorn
from utils.youtube_subtitle import get_subtitle_text

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/test")
async def test_endpoint():
    return {"status": "success", "message": "API is reachable"}

@app.post("/process_youtube")
async def process_youtube(req: YouTubeRequest, background_tasks: BackgroundTasks):
    try:
        video_url = extract_youtube_stream_url(req.url)
        background_tasks.add_task(process_video, video_url)
        
        logger.info(f"처리 요청 수신 및 백그라운드 작업 시작: {video_url}")
        
        return {"status": "processing started", "video_url": video_url}
    except Exception as e:
        logger.error(f"처리 요청 중 예외 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# 자막 요청을 위한 모델 (URL과 언어)
class SubtitleRequest(BaseModel):
    url: str
    lang: str = "ko"

@app.post("/get_subtitle")
async def get_subtitle(req: SubtitleRequest):
    try:
        subtitle_text = get_subtitle_text(req.url, req.lang)
        if not subtitle_text:
            raise HTTPException(status_code=404, detail=f"'{req.lang}' 자막이 없습니다.")
        return {"status": "success", "subtitle": subtitle_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # 외부 접근을 위해 host를 0.0.0.0 또는 할당된 외부 IP로, 포트는 GCP 방화벽에 맞춰 설정
    uvicorn.run(app, host="34.64.54.31", port=5000)
