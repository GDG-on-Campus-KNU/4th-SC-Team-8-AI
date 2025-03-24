import re
from pydantic import BaseModel, Field, field_validator

YOUTUBE_URL_REGEX = r"^(https://www\.youtube\.com/watch\?v=[\w-]+|https://youtu\.be/[\w-]+)$"

class YouTubeRequest(BaseModel):
    url: str = Field(..., pattern=YOUTUBE_URL_REGEX)

    @field_validator("url")
    def validate_url(cls, v):
        if not re.match(r"^https://www\.youtube\.com/watch\?v=[\w-]+$", v):
            raise ValueError("유튜브 링크 형식이 올바르지 않습니다.")
        return v
