from abc import ABC
from hashlib import sha256

import tornado.ioloop
import tornado.web
from sqlalchemy import create_engine, select, Table, Column, Integer, String, MetaData, DateTime
from datetime import datetime

import yaml


class BaseHandler(tornado.web.RequestHandler, ABC):
    """Хэндлер-предок для проверки куков"""
    def get_current_user(self):
        return self.get_secure_cookie("mycookie")


class AuthHandler(BaseHandler, ABC):
    """Хэндлер для аутенфикации"""
    def post(self):
        self.set_header("Content-Type", "application/json")
        input_ = self.get_argument("pass")
        sha_entered_pass = sha256(input_.encode('utf-8')).hexdigest()
        url = "postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}".format(
            DB_USERNAME=d["DB_USERNAME"], DB_PASSWORD=d["DB_PASSWORD"], DB_NAME=d["DB_NAME"])
        engine = create_engine(url)
        conn = engine.connect()
        # поиск логина в базе данных
        s = select([users]).where(users.c.login == self.get_argument("login"))
        r = conn.execute(s)
        row = r.fetchone()
        if not row:
            # если такого логина нет – ошибка
            raise tornado.web.HTTPError(404)
        else:
            if sha_entered_pass == row[2]:
                if not self.get_secure_cookie("mycookie"):
                    # если пароль правильный и куки не установлены – устанавливаем
                    self.set_secure_cookie("mycookie", self.get_argument("login"))
            else:
                # если пароль неправильный – ошибка
                raise tornado.web.HTTPError(404)


class GetDataHandler(BaseHandler, ABC):
    """Хэндлер для отправки данных из таблицы"""
    def get(self):
        if not self.current_user:
            # Если пользователь не авторизован – ошибка
            raise tornado.web.HTTPError(401)
        url = "postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}".format(
            DB_USERNAME=d["DB_USERNAME"], DB_PASSWORD=d["DB_PASSWORD"], DB_NAME=d["DB_NAME"])
        engine = create_engine(url)
        conn = engine.connect()
        s = select([collected_data])
        r = conn.execute(s)

        # названия полей таблицы
        titles: list = ['id', 'COUNTRY', 'COUNTRY CODE', 'ISO CODES', 'POPULATION', 'AREA KM', 'GDP $USD']

        # словарь для вывода информации
        out_dict: dict = {"data": [],
                          "total": 0
                          }

        # счетчик кол-ва записей
        total: int = 0
        # заполнение словаря out_dict для ответа на запрос
        for row in r:
            total += 1
            title_pointer: int = 0
            row_dict: dict = {}
            for item in row:
                row_dict[titles[title_pointer]] = item
                title_pointer += 1
            out_dict["data"].append(row_dict)
        out_dict["total"] = total
        conn.close()
        self.set_header("Content-type", "application/json")
        self.write(out_dict)


if __name__ == "__main__":
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

    with open(r"/Users/elenakozenko/Desktop/task_job/config.yaml", "r") as file:
        d = yaml.safe_load(file)

    application = tornado.web.Application([
        (r"/api/login", AuthHandler),
        (r"/api/data", GetDataHandler),
    ], cookie_secret="lkdsjflaksh34234kljaskjdn"
    )
    application.listen(d["TORNADO_PORT"])
    tornado.ioloop.IOLoop.current().start()
