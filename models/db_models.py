from sqlalchemy import Column, BigInteger, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Landmark(Base):
    __tablename__ = "game"  

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # auto_increment, primary key
    landmark = Column(Text, nullable=False)  # mediumtext (NOT NULL)
    youtube_link = Column(String(255), unique=True, nullable=False)  # varchar(255), UNIQUE, NOT NULL