# from pydantic import BaseModel
# from typing import Optional, List

# class ProcessResponse(BaseModel):
#     status: str
#     video_url: str

# class SubtitleResponse(BaseModel):
#     status: str
#     subtitle: str

# class TestResponse(BaseModel):
#     status: str
#     message: str
from typing import List, Dict
from pydantic import BaseModel


class ProcessResponse(BaseModel):
    status: str
    video_url: str


class SubtitleResponse(BaseModel):
    status: str
    youtube_id: str
    captions: List[Dict]
    file_path: str
    static_url: str


class TestResponse(BaseModel):
    status: str
    message: str


class EvaluateResponse(BaseModel):
    score: float  # DTW 거리 (작을수록 좋음)
    rating: str   # good / great / perfect / no_data
