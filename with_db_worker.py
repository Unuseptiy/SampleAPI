from typing import Dict, Union

from sqlalchemy.exc import NoResultFound

from database.get_engine import Session
from database.db_init import CollectedData, Users


def get_data() -> Dict[str, Union[list, int]]:
    session = Session()
    data_about_countries = session.query(CollectedData.id, CollectedData.country, CollectedData.country_code,
                                         CollectedData.iso_codes, CollectedData.population, CollectedData.area,
                                         CollectedData.gdp).all()

    # dictionary for inference the information
    out_dict = {"data": [],
                "total": 0
                }

    # counter of the number of records in collected_data
    total = len(data_about_countries)

    # names of the table fields
    titles = ['id', 'country', 'country_code', 'iso_codes', 'population', 'area', 'gdp']

    # out_dict dictionary filling for response
    for row in data_about_countries:
        row_dict = {}
        i = 0
        for title in titles:
            row_dict[title] = row[i]
            i += 1
        out_dict["data"].append(row_dict)
    out_dict["total"] = total

    return out_dict


def is_valid_user(login: str, password: str) -> bool:
    session = Session()
    # finding login in database
    try:
        session.query(Users).filter(Users.login == login, Users.password == password).one()
        return True
    except NoResultFound:
        return False

