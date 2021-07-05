from abc import ABC
from hashlib import sha256

import tornado.ioloop
import tornado.web
from sqlalchemy import create_engine, select, update
import os

import yaml
from sqlalchemy.orm import Session
from db_init import CollectedData, Users


class BaseHandler(tornado.web.RequestHandler, ABC):
    """Parent Handler for checking cookies"""
    def get_current_user(self):
        return self.get_secure_cookie("mycookie")


class AuthHandler(BaseHandler, ABC):
    """Handler for authentication"""
    def post(self):
        self.set_header("Content-Type", "application/json")
        input_pass = self.get_argument("pass")
        sha_entered_pass = sha256(input_pass.encode('utf-8')).hexdigest()
        input_login = self.get_argument("login")

        # finding login in database
        person = session.query(Users).filter(Users.login == input_login).first()
        if not person:
            # if this username does not exist – an error
            raise tornado.web.HTTPError(404)
        else:
            session.query(Users).filter(Users.login == input_login).update({"login": input_login}, synchronize_session='fetch')
            session.commit()
            if sha_entered_pass == person.password:
                if not self.get_secure_cookie("mycookie"):
                    # setting a cookie if the password is correct and the cookie is not set
                    self.set_secure_cookie("mycookie", self.get_argument("login"))
            else:
                # if this password is incorrect – an error
                raise tornado.web.HTTPError(404)


class GetDataHandler(BaseHandler, ABC):
    """Handler for sending data from the collected_data table"""
    def get(self):
        if not self.current_user:
            # If the user is not authenticated, an error occurs
            raise tornado.web.HTTPError(401)

        data_about_countries = session.query(CollectedData).all()

        # names of the table fields
        titles = ['id', 'country', 'country_code', 'iso_codes', 'population', 'area', 'gdp']

        # dictionary for inference the information
        out_dict: dict = {"data": [],
                          "total": 0
                          }

        # counter of the number of records in collected_data
        total = len(data_about_countries)

        # out_dict dictionary filling for response
        for row in data_about_countries:
            row_dict: dict = {}
            for title in titles:
                row_dict[title] = getattr(row, title)
            out_dict["data"].append(row_dict)
        out_dict["total"] = total
        self.set_header("Content-type", "application/json")
        self.write(out_dict)


if __name__ == "__main__":
    path = os.getcwd()
    with open(os.path.join(path, "../config.yaml"), "r") as file:
        d = yaml.safe_load(file)

    url = "postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}".format(DB_USERNAME=d["DB_USERNAME"],
                                                                                         DB_PASSWORD=d["DB_PASSWORD"],
                                                                                         DB_NAME=d["DB_NAME"])
    engine = create_engine(url)
    session = Session(bind=engine)

    application = tornado.web.Application([
        (r"/api/login", AuthHandler),
        (r"/api/data", GetDataHandler),
    ], cookie_secret="lkdsjflaksh34234kljaskjdn"
    )
    application.listen(d["TORNADO_PORT"])
    tornado.ioloop.IOLoop.current().start()
