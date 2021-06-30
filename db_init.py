from sqlalchemy import create_engine, MetaData, Table, Integer, String, Column, DateTime
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy_utils import database_exists
import yaml


with open(r"/Users/elenakozenko/Desktop/task_job/config.yaml", "r") as file:
    d = yaml.safe_load(file)

url = "postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}".format(DB_USERNAME=d["DB_USERNAME"],
                                                                                     DB_PASSWORD=d["DB_PASSWORD"],
                                                                                     DB_NAME=d["DB_NAME"])

if not database_exists(url):
    # database creating
    connection = psycopg2.connect(user="postgres", password="1111")
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    sql_create_database = cursor.execute('create database countries_db')
    cursor.close()
    connection.close()

engine = create_engine(url)
metadata = MetaData()
# creating database tables
collected_data = Table('collected_data', metadata,
                       Column('id', Integer(), primary_key=True, nullable=False),
                       Column('country', String(100), nullable=False),
                       Column('country_code', String(50), nullable=False),
                       Column('iso_codes', String(50), nullable=False),
                       Column('population', String(200)),
                       Column('area', String(200), nullable=False),
                       Column('gdp', String(50)),
                       )

users = Table('users', metadata,
              Column('id', Integer(), primary_key=True, nullable=False),
              Column('login', String(100), unique=True, nullable=False),
              Column('password', String(100), nullable=False),
              Column('created_at', DateTime(), default=datetime.utcnow(), nullable=False),
              Column('last_request', DateTime(), onupdate=datetime.utcnow())
              )
metadata.create_all(engine)
