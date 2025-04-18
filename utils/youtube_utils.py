import yt_dlp
from utils.logging_utils import logger

def extract_youtube_stream_url(youtube_url: str) -> str:
    try:
        logger.info(f"스트리밍 URL 추출 시작: {youtube_url}")

        ydl_opts = {'quiet': True, 'format': 'best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            video_url = info['url']

        logger.info(f"스트리밍 URL 추출 완료: {video_url}")
        return video_url

    except Exception as e:
        logger.error(f"스트리밍 URL 추출 실패: {e}", exc_info=True)
        raise
