from abc import ABC
from hashlib import sha256
import tornado.ioloop
import tornado.web

from database.get_engine import Session, TORNADO_PORT, SALT
from with_db_worker import is_valid_user, get_data


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

        if not self.get_secure_cookie("mycookie"):
            if is_valid_user(input_login, sha_entered_pass):
                self.set_secure_cookie("mycookie", input_login)
            else:
                raise tornado.web.HTTPError(404)


class GetDataHandler(BaseHandler, ABC):
    """Handler for sending data from the collected_data table"""
    def get(self):
        if not self.current_user:
            # If the user is not authenticated, an error occurs
            raise tornado.web.HTTPError(401)
        out_dict = get_data()
        self.set_header("Content-type", "application/json")
        self.write(out_dict)


if __name__ == "__main__":
    session = Session()

    application = tornado.web.Application([
        (r"/api/login", AuthHandler),
        (r"/api/data", GetDataHandler),
    ], cookie_secret=SALT
    )
    application.listen(TORNADO_PORT)
    tornado.ioloop.IOLoop.current().start()
