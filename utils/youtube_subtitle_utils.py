# import yt_dlp
# import requests

# def get_subtitle_text(youtube_url: str, lang="ko"):
#     ydl_opts = {'quiet': True}

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(youtube_url, download=False)
#         subtitles = info.get("subtitles", {})

#         # 요청한 언어의 자막이 있는지 확인
#         if lang not in subtitles:
#             print(f"⚠️ '{lang}' 자막이 없습니다.")
#             return None

#         # 자막 URL 가져오기
#         subtitle_url = subtitles[lang][0]['url']

#         # 자막 데이터 가져오기 (XML 또는 SRT 형식)
#         response = requests.get(subtitle_url)
#         subtitle_text = response.text

#         print(f"📌 {lang} 자막 미리보기:")
#         print(subtitle_text[:500])  # 자막 일부만 출력

#         return subtitle_text

# # # standalone 테스트용 코드 (원하는 경우)
# # if __name__ == '__main__':
# #     youtube_url = "https://www.youtube.com/watch?v=28kn2IQEWRk"
# #     subtitle_text = get_subtitle_text(youtube_url, lang="ko")
# #     print(subtitle_text)

"""
YouTube 자막을 내려받아 start / dur / text 정보를
JSON 으로 저장하고 (captions, file_path) 를 반환한다.
"""
from __future__ import annotations

import os
import re
import json
import time
import requests
import xml.etree.ElementTree as ET
from html import unescape
from typing import List, Dict, Tuple, Optional

import yt_dlp
from utils.logging_utils import logger

# ---------------------------------------------------------------------
# 공통 설정
# ---------------------------------------------------------------------
_SUBTITLE_DIR = os.path.join("output", "subtitles")
os.makedirs(_SUBTITLE_DIR, exist_ok=True)

# ---------------------------------------------------------------------
# srv3 / ttml 파싱
# ---------------------------------------------------------------------
def _parse_srv3(xml_text: str) -> List[Dict]:
    """<text start="…" dur="…"> 형식의 XML(srv3/ttml) 파싱."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        logger.warning("[XML 파싱 실패] srv3/ttml 포맷 아님")
        return []

    captions: List[Dict] = []
    for elem in root.findall(".//text"):
        try:
            start = float(elem.attrib.get("start", 0))
            dur = float(elem.attrib.get("dur", 0))
            txt = unescape(elem.text or "").replace("\n", " ").strip()
            captions.append({"start": start, "dur": dur, "text": txt})
        except ValueError:
            continue
    return captions

# ---------------------------------------------------------------------
# VTT 파싱
# ---------------------------------------------------------------------
_VTT_TIMESTAMP_RE = re.compile(
    r"(?P<h>\d{2}):(?P<m>\d{2}):(?P<s>\d{2})\.(?P<ms>\d{3})"
)


def _vtt_ts_to_sec(ts: str) -> float:
    m = _VTT_TIMESTAMP_RE.search(ts)
    if not m:
        return 0.0
    h, m_, s, ms = map(int, m.groups())
    return h * 3600 + m_ * 60 + s + ms / 1000


def _parse_vtt(vtt_text: str) -> List[Dict]:
    lines = [l.rstrip("\r") for l in vtt_text.splitlines()]
    captions: List[Dict] = []
    cur: Optional[Dict] = None

    for ln in lines:
        if "-->" in ln and _VTT_TIMESTAMP_RE.search(ln):
            if cur:  # 이전 캡션 push
                captions.append(cur)
            ts_from, ts_to = [t.strip() for t in ln.split("-->")]
            cur = {
                "start": _vtt_ts_to_sec(ts_from),
                "dur": None,
                "text": "",
            }
            end_time = _vtt_ts_to_sec(ts_to)
            if end_time > cur["start"]:
                cur["dur"] = end_time - cur["start"]
        elif ln.strip() == "":
            if cur and cur["text"]:
                captions.append(cur)
                cur = None
        else:
            # 자막 텍스트 라인
            if cur is not None:
                cur["text"] += (ln + " ")

    # 파일 끝 처리
    if cur and cur["text"]:
        captions.append(cur)

    # dur 없는 캡션 보정 (다음 캡션 시작 - 현재 시작)
    for i in range(len(captions) - 1):
        if captions[i]["dur"] is None:
            captions[i]["dur"] = (
                captions[i + 1]["start"] - captions[i]["start"]
            )
    return captions

# ---------------------------------------------------------------------
# JSON 저장
# ---------------------------------------------------------------------
def _save_json(info: dict, lang: str, captions: List[Dict]) -> str:
    youtube_id = info.get("id", "unknown")
    title = info.get("title") or ""
    ts = int(time.time())
    fname = f"{youtube_id}_{ts}.json"
    fpath = os.path.join(_SUBTITLE_DIR, fname)

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(
            {
                "youtube_id": youtube_id,
                "title": title,
                "lang": lang,
                "captions": captions,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    logger.info(f"[자막 저장 완료] {fpath}")
    return os.path.abspath(fpath)

# ---------------------------------------------------------------------
# 메인 함수
# ---------------------------------------------------------------------
def get_subtitle_with_timing(
    youtube_url: str,
    lang: str = "ko",
) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    (captions, file_path) 반환.
    자막 트랙을 순차적으로 시도해, 파싱 성공 시 즉시 반환.
    """
    ydl_opts = {"quiet": True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False)

    # ---------- 트랙 후보 수집 ----------
    def _collect_tracks(source_dict: dict) -> List[dict]:
        tracks: List[dict] = []
        for code, lst in source_dict.items():
            # 요청 언어와 정확히 일치하거나, 'ko-KR' 처럼 접두사가 같은 경우 포함
            if code == lang or code.startswith(f"{lang}-") or code.split("-")[0] == lang:
                tracks.extend(lst)
        return tracks

    tracks = (
        _collect_tracks(info.get("subtitles", {}))
        + _collect_tracks(info.get("automatic_captions", {}))
    )
    if not tracks:
        logger.warning(f"[자막 트랙 없음] {lang=} {youtube_url=}")
        return None, None

    # ---------- 확장자 우선순위 ----------
    ext_priority = {"srv3": 0, "ttml": 1, "vtt": 2}
    tracks.sort(key=lambda t: ext_priority.get(t.get("ext"), 99))

    # ---------- 각 트랙 시도 ----------
    for t in tracks:
        url = t["url"]
        ext = t.get("ext")
        # srv3 강제 파라미터
        if ext == "srv3" and "fmt=" not in url:
            url += "&fmt=srv3"

        logger.info(f"[자막 다운로드] ext={ext} url={url}")
        try:
            res = requests.get(url, timeout=10)
            res.raise_for_status()
            raw = res.text
        except Exception:
            logger.error("[자막 다운로드 실패]", exc_info=True)
            continue

        # --- 파싱 ---
        if ext in ("srv3", "ttml") or "<text" in raw[:200]:
            captions = _parse_srv3(raw)
        elif ext == "vtt" or raw.lstrip().startswith("WEBVTT"):
            captions = _parse_vtt(raw)
        else:
            logger.warning(f"[알 수 없는 포맷] ext={ext}")
            captions = []

        # 파싱 성공 여부 확인
        if captions:
            file_path = _save_json(info, lang, captions)
            return captions, file_path
        else:
            logger.warning(f"[파싱 실패] ext={ext} → 다음 트랙 시도")

    # 모든 트랙 파싱 실패
    logger.error("[자막 파싱 실패] 모든 트랙에서 captions 추출 불가")
    return None, None
