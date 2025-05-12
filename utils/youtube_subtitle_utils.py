import requests
import json
from utils.logging_utils import logger
from yt_dlp import YoutubeDL

def get_manual_subtitle_text(youtube_url: str, lang="ko"):
    ydl_opts = {
        'quiet': True,
        'writesubtitles': True,       # 수동 자막만
        'writeautomaticsub': False,   # 자동 자막 무시
        'subtitlesformat': 'json3'
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        subtitles = info.get("subtitles", {})

        if lang not in subtitles:
            logger.warning(f"'{lang}' 수동 자막이 없습니다.")
            return None

        subtitle_url = subtitles[lang][0]['url']
        response = requests.get(subtitle_url)
        subtitle_text = response.text

        try:
            subtitle_json = json.loads(subtitle_text)
        except json.JSONDecodeError:
            logger.error("자막 JSON 파싱 실패")
            return None

        logger.info(f"'{lang}' 수동 자막 성공적으로 파싱됨")
        return subtitle_json