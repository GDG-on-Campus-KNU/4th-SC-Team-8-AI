import glob, os, json
from typing import Optional

def find_latest_json(youtube_id: str) -> Optional[str]:
    paths = glob.glob(os.path.join("output", "youtube_result",
                                   f"*{youtube_id}*.json"))
    return max(paths, key=os.path.getmtime) if paths else None

def is_ready(youtube_id: str) -> bool:
    """랜드마크 JSON 존재 && data 길이 > 0"""
    path = find_latest_json(youtube_id)
    if not path:
        return False
    try:
        with open(path, encoding="utf-8") as f:
            obj = json.load(f)
        return bool(obj.get("data"))
    except Exception:
        return False
