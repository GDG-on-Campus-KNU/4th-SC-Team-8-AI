from sqlalchemy.orm import Session
from models import db_models, request_models

def create_landmark(db: Session, landmark: request_models.LandmarkCreate):
    db_landmark = db_models.Landmark(landmark=landmark.landmark, youtube_link=landmark.youtube_link)
    db.add(db_landmark)
    db.commit()
    db.refresh(db_landmark)
    return db_landmark

def get_landmark(db: Session, landmark_id: int):
    return db.query(db_models.Landmark).filter(db_models.Landmark.id == landmark_id).first()

def get_landmarks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(db_models.Landmark).offset(skip).limit(limit).all()

def get_landmark_by_url(db: Session, youtube_link: str):
    return db.query(db_models.Landmark).filter(db_models.Landmark.youtube_link == youtube_link).first()

def update_landmark(db: Session, landmark_id: int, landmark: request_models.LandmarkCreate):
    db_landmark = db.query(db_models.Landmark).filter(db_models.Landmark.id == landmark_id).first()
    if db_landmark:
        db_landmark.landmark = landmark.landmark
        db_landmark.youtube_link = landmark.youtube_link
        db.commit()
        db.refresh(db_landmark)
    return db_landmark

def delete_landmark(db: Session, landmark_id: int):
    db_landmark = db.query(db_models.Landmark).filter(db_models.Landmark.id == landmark_id).first()
    if db_landmark:
        db.delete(db_landmark)
        db.commit()
    return db_landmark