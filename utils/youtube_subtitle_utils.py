import yt_dlp
import requests

def get_subtitle_text(youtube_url: str, lang="ko"):
    ydl_opts = {'quiet': True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        subtitles = info.get("subtitles", {})

        # 요청한 언어의 자막이 있는지 확인
        if lang not in subtitles:
            print(f"⚠️ '{lang}' 자막이 없습니다.")
            return None

        # 자막 URL 가져오기
        subtitle_url = subtitles[lang][0]['url']

        # 자막 데이터 가져오기 (XML 또는 SRT 형식)
        response = requests.get(subtitle_url)
        subtitle_text = response.text

        print(f"📌 {lang} 자막 미리보기:")
        print(subtitle_text[:500])  # 자막 일부만 출력

        return subtitle_text

# # standalone 테스트용 코드 (원하는 경우)
# if __name__ == '__main__':
#     youtube_url = "https://www.youtube.com/watch?v=28kn2IQEWRk"
#     subtitle_text = get_subtitle_text(youtube_url, lang="ko")
#     print(subtitle_text)
