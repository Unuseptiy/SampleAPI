# scraper.py
import argparse
import requests
from bs4 import BeautifulSoup
from pyparsing import *
import pandas as pd
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, select, delete
from tabulate import tabulate
from datetime import datetime
import yaml


def get_title(soup_obj: BeautifulSoup) -> list:
    """Парсит BeautifulSoup объект и возвращает поля таблицы"""
    quote = soup_obj.find_all('th')
    title_word_parser = Word(alphas) + ZeroOrMore(' ') + ZeroOrMore(Word(alphas + '$'))
    titles_func: list = []
    for title_func in quote:
        titles_func.append(' '.join(title_word_parser.parseString(title_func.text).asList()))
    for i_func in [1] * 3:
        del titles_func[-i_func]
    return titles_func


def str2bool(v):
    """Преобразует введенный аргумент коммандной строки в требуемый вид, либо возвращает ошибку"""
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

url = 'https://countrycode.org'
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

# в data получаем данные из всех таблиц
data = soup.find_all('tbody')

titles: list = get_title(soup)

# инициализация table_dict – словарь, в котром ключи – названия полей таблицы, значения – списки значений в
# соответствующих полях
table_dict: dict = {}
for title in titles:
    table_dict[title] = []

# заполнение table_dict
i: int = 0
for string in data[0].text.split(sep='\n'):
    index = i % 8 - 2
    if index != -2 and index != -1:
        table_dict[titles[index]].append(string)
    i += 1

df = pd.DataFrame(data=table_dict)

# добавление аргумента в парсер аргументов командной строки
parser = argparse.ArgumentParser()
parser.add_argument("--dry_run", type=str2bool, nargs='?', const=True, default=False, help="A flag, that describes, "
                                                                                           "where table has been "
                                                                                           "stored: in database or "
                                                                                           "prints in console")

if parser.parse_args().dry_run:
    # Если --dry_run True, то таблица выводится в консоль
    print(tabulate(df, headers='keys', tablefmt='psql'))
else:
    # иначе сохраняется в базу данных
    with open(r"/Users/elenakozenko/Desktop/task_job/config.yaml", "r") as file:
        d = yaml.safe_load(file)

    url = "postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}".format(DB_USERNAME=d["DB_USERNAME"],
                                                                                         DB_PASSWORD=d["DB_PASSWORD"],
                                                                                         DB_NAME=d["DB_NAME"])
    engine = create_engine(url)
    metadata = MetaData()

    # создание таблицы collected_data
    collected_data = Table('collected_data', metadata,
                           Column('id', Integer(), primary_key=True, nullable=False),
                           Column('country', String(100), nullable=False),
                           Column('country_code', String(50), nullable=False),
                           Column('iso_codes', String(50), nullable=False),
                           Column('population', String(200)),
                           Column('area', String(200), nullable=False),
                           Column('gdp', String(50)),
                           )

    # создание таблицы users
    users = Table('users', metadata,
                  Column('id', Integer(), primary_key=True, nullable=False),
                  Column('login', String(100), unique=True, nullable=False),
                  Column('password', String(100), nullable=False),
                  Column('created_at', DateTime(), default=datetime.utcnow(), nullable=False),
                  Column('last_request', DateTime())
                  )
    conn = engine.connect()
    s = select([collected_data])
    r = conn.execute(s)

    # проверка: пуста ли таблица collected_data
    if r.fetchall():
        # удаление всех записей из таблицы collected_data
        s = delete(collected_data)
        rs = conn.execute(s)

    # добавление записей в таблицу collected_data
    for i in range(len(table_dict[next(iter(table_dict))])):
        ins = collected_data.insert().values(
            id=i,
            country=table_dict['COUNTRY'][i],
            country_code=table_dict['COUNTRY CODE'][i],
            iso_codes=table_dict['ISO CODES'][i],
            population=table_dict['POPULATION'][i],
            area=table_dict['AREA KM'][i],
            gdp=table_dict['GDP $USD'][i],
        )
        r = conn.execute(ins)
    conn.close()
