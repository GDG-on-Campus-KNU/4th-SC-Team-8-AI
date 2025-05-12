# utils/common.py
"""
공통 유틸: YouTube URL에서 11자리 영상 ID 추출
"""
import re

# 모든 YouTube URL 형태 지원 (youtu.be, watch?v=, embed/ 등)
_ID_RE = re.compile(
    r"(?:youtu\.be/|youtube\.com/(?:embed/|v/|watch\?v=))"
    r"([A-Za-z0-9_-]{11})"
)

def extract_yt_id(url: str) -> str:
    """
    >>> extract_yt_id("https://youtu.be/ABCdefGhijk?t=30")
    'ABCdefGhijk'
    """
    m = _ID_RE.search(url)
    return m.group(1) if m else ""
