from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


DATABASE_URL = "sqlite:///./smart_home.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    device_id = Column(String, unique=True, index=True)
    status = Column(String, default="off")

def init_db():
    Base.metadata.create_all(bind=engine)
