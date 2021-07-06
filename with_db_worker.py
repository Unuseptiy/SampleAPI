from database.get_engine import Session
from database.db_init import CollectedData, Users


def get_data() -> dict:
    session = Session()
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
    return out_dict


def is_valid_user(login: str, password: str) -> bool:
    session = Session()
    # finding login in database
    person = session.query(Users).filter(Users.login == login).first()
    if not person:
        # if this username does not exist – an error
        return False
    else:
        if password == person.password:
            # setting last_request
            session.query(Users).filter(Users.login == login).update({"login": login},
                                                                     synchronize_session='fetch')
            session.commit()
            return True
        else:
            # if this password is incorrect – an error
            return False