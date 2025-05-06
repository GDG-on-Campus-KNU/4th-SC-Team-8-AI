from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from models import db_models, request_models

async def create_game(db: AsyncSession, game: request_models.GameCreate):
    db_game = db_models.Game(landmark=game.landmark, youtube_link=game.youtube_link)
    db.add(db_game)
    await db.commit()
    await db.refresh(db_game)
    return db_game

async def game(db: AsyncSession, game_id: int):
    result = await db.execute(select(db_models.Game).where(db_models.Game.id == game_id))
    return result.scalar_one_or_none()

async def get_games(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(db_models.Game).offset(skip).limit(limit))
    return result.scalars().all()

async def get_game_by_url(db: AsyncSession, youtube_link: str):
    result = await db.execute(select(db_models.Game).where(db_models.Game.youtube_link == youtube_link))
    return result.scalar_one_or_none()

async def update_game(db: AsyncSession, game_id: int, game: request_models.GameCreate):
    result = await db.execute(select(db_models.Game).where(db_models.Game.id == game_id))
    db_game = result.scalar_one_or_none()
    if db_game:
        db_game.landmark = game.landmark
        db_game.youtube_link = game.youtube_link
        await db.commit()
        await db.refresh(db_game)
    return db_game

async def delete_game(db: AsyncSession, game_id: int):
    result = await db.execute(select(db_models.Game).where(db_models.Game.id == game_id))
    db_game = result.scalar_one_or_none()
    if db_game:
        await db.delete(db_game)
        await db.commit()
    return db_game
