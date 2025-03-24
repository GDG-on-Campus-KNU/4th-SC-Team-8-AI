from sqlalchemy.orm import Session
from db.session import SessionLocal
from crud.landmark import create_landmark
from models import request_models

def test_create_landmark():
    # 1. DB 세션 생성
    db: Session = SessionLocal()

    # 2. 테스트용 Landmark 데이터 준비
    test_data = request_models.LandmarkCreate(
        youtube_link="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        landmark='{"status": "processed", "total_frames_processed": 1}'
    )

    try:
        # 3. Landmark 저장
        saved = create_landmark(db, landmark=test_data)

        # 4. 결과 출력
        print("✅ Landmark 저장 성공")
        print(f"ID: {saved.id}")
        print(f"YouTube URL: {saved.youtube_link}")
        print(f"Landmark 데이터: {saved.landmark[:100]}...")  # 너무 길면 일부만

    except Exception as e:
        print("❌ Landmark 저장 실패:", e)

    finally:
        db.close()

if __name__ == "__main__":
    test_create_landmark()
