# from sqlalchemy.orm import Session
# from models import db_models, request_models

# def create_game(db: Session, game: request_models.GameCreate):
#     db_game = db_models.Game(landmark=game.landmark, youtube_link=game.youtube_link)
#     db.add(db_game)
#     db.commit()
#     db.refresh(db_game)
#     return db_game

# def game(db: Session, game_id: int):
#     return db.query(db_models.Game).filter(db_models.Game.id == game_id).first()

# def get_games(db: Session, skip: int = 0, limit: int = 100):
#     return db.query(db_models.Game).offset(skip).limit(limit).all()

# def get_game_by_url(db: Session, youtube_link: str):
#     return db.query(db_models.Game).filter(db_models.Game.youtube_link == youtube_link).first()

# def update_game(db: Session, game_id: int, game: request_models.GameCreate):
#     db_game = db.query(db_models.Game).filter(db_models.Game.id == game_id).first()
#     if db_game:
#         db_game.landmark = game.landmark
#         db_game.youtube_link = game.youtube_link
#         db.commit()
#         db.refresh(db_game)
#     return db_game

# def delete_game(db: Session, game_id: int):
#     db_game = db.query(db_models.Game).filter(db_models.Game.id == game_id).first()
#     if db_game:
#         db.delete(db_game)
#         db.commit()
#     return db_game


from sqlalchemy.orm import Session
from models.db_models import Game
from models.request_models import GameCreate


def create_game(db: Session, game: GameCreate):
    db_game = Game(
        landmark=game.landmark,
        youtube_link=game.youtube_link,
    )
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game


def game(db: Session, game_id: int):
    return db.query(Game).filter(Game.id == game_id).first()


def get_games(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Game).offset(skip).limit(limit).all()


def get_game_by_url(db: Session, youtube_link: str):
    return db.query(Game).filter(Game.youtube_link == youtube_link).first()


# ---------- 추가: youtube_id 로 검색 ----------
def get_game_by_video_id(db: Session, youtube_id: str):
    like_pattern = f"%{youtube_id}%"
    return db.query(Game).filter(Game.youtube_link.like(like_pattern)).first()


def update_game(db: Session, game_id: int, game: GameCreate):
    db_game = db.query(Game).filter(Game.id == game_id).first()
    if db_game:
        db_game.landmark = game.landmark
        db_game.youtube_link = game.youtube_link
        db.commit()
        db.refresh(db_game)
    return db_game


def delete_game(db: Session, game_id: int):
    db_game = db.query(Game).filter(Game.id == game_id).first()
    if db_game:
        db.delete(db_game)
        db.commit()
    return db_game
