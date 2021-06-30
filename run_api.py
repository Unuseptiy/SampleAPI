from abc import ABC
from hashlib import sha256

import tornado.ioloop
import tornado.web
from sqlalchemy import create_engine, select, Table, Column, Integer, String, MetaData, DateTime
from datetime import datetime

import yaml


class BaseHandler(tornado.web.RequestHandler, ABC):
    """Parent Handler for checking cookies"""
    def get_current_user(self):
        return self.get_secure_cookie("mycookie")


class AuthHandler(BaseHandler, ABC):
    """Handler for authentication"""
    def post(self):
        self.set_header("Content-Type", "application/json")
        input_ = self.get_argument("pass")
        sha_entered_pass = sha256(input_.encode('utf-8')).hexdigest()
        url = "postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}".format(
            DB_USERNAME=d["DB_USERNAME"], DB_PASSWORD=d["DB_PASSWORD"], DB_NAME=d["DB_NAME"])
        engine = create_engine(url)
        conn = engine.connect()
        # finding login in database
        s = select([users]).where(users.c.login == self.get_argument("login"))
        r = conn.execute(s)
        row = r.fetchone()
        if not row:
            # if this username does not exist – an error
            raise tornado.web.HTTPError(404)
        else:
            if sha_entered_pass == row[2]:
                if not self.get_secure_cookie("mycookie"):
                    # setting a cookie if the password is correct and the cookie is not set
                    self.set_secure_cookie("mycookie", self.get_argument("login"))
            else:
                # if this password is incorrect – an error
                raise tornado.web.HTTPError(404)
        conn.close()


class GetDataHandler(BaseHandler, ABC):
    """Handler for sending data from the collected_data table"""
    def get(self):
        if not self.current_user:
            # If the user is not authenticated, an error occurs
            raise tornado.web.HTTPError(401)
        url = "postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}".format(
            DB_USERNAME=d["DB_USERNAME"], DB_PASSWORD=d["DB_PASSWORD"], DB_NAME=d["DB_NAME"])
        engine = create_engine(url)
        conn = engine.connect()
        s = select([collected_data])
        r = conn.execute(s)

        # names of the table fields
        titles: list = ['id', 'COUNTRY', 'COUNTRY CODE', 'ISO CODES', 'POPULATION', 'AREA KM', 'GDP $USD']

        # dictionary for inference the information
        out_dict: dict = {"data": [],
                          "total": 0
                          }

        # counter of the number of records in collected_data
        total: int = 0

        # out_dict dictionary filling for response
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
    # creating collected_data table
    collected_data = Table('collected_data', metadata,
                           Column('id', Integer(), primary_key=True, nullable=False),
                           Column('country', String(100), nullable=False),
                           Column('country_code', String(50), nullable=False),
                           Column('iso_codes', String(50), nullable=False),
                           Column('population', String(200)),
                           Column('area', String(200), nullable=False),
                           Column('gdp', String(50)),
                           )

    # creating users table
    users = Table('users', metadata,
                  Column('id', Integer(), primary_key=True, nullable=False),
                  Column('login', String(100), unique=True, nullable=False),
                  Column('password', String(100), nullable=False),
                  Column('created_at', DateTime(), default=datetime.utcnow(), nullable=False),
                  Column('last_request', DateTime())
                  )

    with open(r"../config.yaml", "r") as file:
        d = yaml.safe_load(file)

    application = tornado.web.Application([
        (r"/api/login", AuthHandler),
        (r"/api/data", GetDataHandler),
    ], cookie_secret="lkdsjflaksh34234kljaskjdn"
    )
    application.listen(d["TORNADO_PORT"])
    tornado.ioloop.IOLoop.current().start()
