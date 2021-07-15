import os
import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

script_dir = os.path.dirname(__file__)
with open(os.path.join(script_dir, "../config.yaml"), "r") as file:
    d = yaml.safe_load(file)

url = "postgresql+psycopg2://{DB_USERNAME}:{DB_PASSWORD}@localhost/{DB_NAME}".format(DB_USERNAME=d["DB_USERNAME"],
                                                                                     DB_PASSWORD=d["DB_PASSWORD"],
                                                                                     DB_NAME=d["DB_NAME"])
engine = create_engine(url)

Session = sessionmaker(bind=engine)

SALT = d["SALT"]
TORNADO_PORT = d["TORNADO_PORT"]
