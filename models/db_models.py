from sqlalchemy import Column, BigInteger, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.dialects.mysql import LONGTEXT

Base = declarative_base()

class Landmark(Base):
    __tablename__ = "game"  

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # auto_increment, primary key
    landmark = Column(LONGTEXT, nullable=False)  # mediumtext (NOT NULL)
    youtube_link = Column(String(255), unique=True, nullable=False)  # varchar(255), UNIQUE, NOT NULL