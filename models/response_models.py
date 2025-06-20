from pydantic import BaseModel
from typing import Optional, List

class ProcessResponse(BaseModel):
    status: str
    video_url: str

class SubtitleResponse(BaseModel):
    status: str 
    subtitle: Optional[dict] = None
    message: str = ""

class TestResponse(BaseModel):
    status: str
    message: str
