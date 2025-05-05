# models/request_models.py

from typing import List
from pydantic import BaseModel, HttpUrl, field_validator, Field
from utils.common import extract_yt_id


class YouTubeRequest(BaseModel):
    url: HttpUrl = Field(..., description="YouTube 링크")

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: HttpUrl) -> HttpUrl:
        # ① HttpUrl → 문자열
        if len(extract_yt_id(str(v))) != 11:
            raise ValueError("유튜브 링크 형식이 올바르지 않습니다.")
        return v


class SubtitleRequest(BaseModel):
    url: HttpUrl
    lang: str = "ko"
