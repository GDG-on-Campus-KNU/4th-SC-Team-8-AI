import json
from typing import Optional

from crud.game import get_latest_game_by_link
from db.session import SessionLocal


def find_latest_json(youtube_id: str) -> Optional[str]:
    """DB에서 가장 최근에 저장된 landmark JSON 문자열을 반환"""
    db = SessionLocal()
    try:
        game = get_latest_game_by_link(db, youtube_id)
        return game.landmark if game and game.landmark else None
    finally:
        db.close()


def is_ready(youtube_id: str) -> bool:
    """랜드마크 JSON 존재 && data 길이 > 0"""
    json_str = find_latest_json(youtube_id)
    if not json_str:
        return False
    try:
        obj = json.loads(json_str)
        return bool(obj.get("data"))
    except Exception:
        return False
