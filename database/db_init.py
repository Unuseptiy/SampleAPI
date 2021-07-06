from sqlalchemy import Integer, String, Column, DateTime
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import database_exists

from database.get_engine import url, engine

Base = declarative_base()


class CollectedData(Base):
    __tablename__ = 'collected_data'
    id = Column(Integer(), primary_key=True, nullable=False)
    country = Column(String(100), nullable=False)
    country_code = Column(String(50), nullable=False)
    iso_codes = Column(String(50), nullable=False)
    population = Column(String(200))
    area = Column(String(200), nullable=False)
    gdp = Column(String(50))


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer(), primary_key=True, nullable=False)
    login = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    created_at = Column(DateTime(), default=datetime.utcnow(), nullable=False)
    last_request = Column(DateTime(), onupdate=datetime.utcnow())


if __name__ == "__main__":
    if not database_exists(url):
        # database creating
        connection = psycopg2.connect(user="postgres", password="1111")
        connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = connection.cursor()
        sql_create_database = cursor.execute('create database countries_db')
        cursor.close()
        connection.close()

    Base.metadata.create_all(engine)
