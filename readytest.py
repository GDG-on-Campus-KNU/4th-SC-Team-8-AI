import json
def is_ready(youtube_id: str) -> bool:
    """랜드마크 JSON 존재 && data 길이 > 0"""
    path = "/home/knuvi/4th-SC-Team-8-AI_minho/output/youtube_result/G0CVDkc5M0M_1746361757.json"
    if not path:
        return False
    try:
        with open(path, encoding="utf-8") as f:
            obj = json.load(f)
        return bool(obj.get("data"))
    except Exception:
        return False

print("debug : ", is_ready("G0CVDkc5M0M"))