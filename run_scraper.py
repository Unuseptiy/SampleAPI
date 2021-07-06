# scraper.py
import argparse

import requests
from bs4 import BeautifulSoup
from pyparsing import *
import pandas as pd
from tabulate import tabulate
from database.db_init import CollectedData
from database.get_engine import Session


def get_title(soup_obj: BeautifulSoup) -> list:
    """Parses the BeautifulSoup object and returns the table fields"""
    quote = soup_obj.find_all('th')
    title_word_parser = Word(alphas) + ZeroOrMore(' ') + ZeroOrMore(Word(alphas + '$'))
    titles_func: list = []
    for title_func in quote:
        titles_func.append(' '.join(title_word_parser.parseString(title_func.text).asList()))
    for i_func in [1] * 3:
        del titles_func[-i_func]
    return titles_func


def str2bool(v):
    """Converts the entered command-line argument to the required form, or returns an error"""
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

# data – data from all tables with <tbody> tag
data = soup.find_all('tbody')

titles: list = get_title(soup)

# initialization of table_dict-a dictionary whose keys are the names of table fields, values are lists of values in the
# corresponding fields
table_dict: dict = {}
for title in titles:
    table_dict[title] = []

# table_dict filling
i: int = 0
for string in data[0].text.split(sep='\n'):
    index = i % 8 - 2
    if index != -2 and index != -1:
        table_dict[titles[index]].append(string)
    i += 1

df = pd.DataFrame(data=table_dict)

# adding an argument to the command line parser
parser = argparse.ArgumentParser()
parser.add_argument("--dry_run", type=str2bool, nargs='?', const=True, default=False, help="A flag describing where the"
                                                                                           " table was saved: in the "
                                                                                           "database or printed in the "
                                                                                           "console")

if parser.parse_args().dry_run:
    # if --dry_run True, then table prints to console
    print(tabulate(df, headers='keys', tablefmt='psql'))
else:
    session = Session()

    data_about_countries = session.query(CollectedData).all()

    # checking whether the collected_data table is empty
    if data_about_countries:
        # удаление всех записей из таблицы collected_data
        # deleting all records from the collected_data table
        session.query(CollectedData).delete(synchronize_session='fetch')
        session.commit()

    # adding records to collected_data table
    for i in range(len(table_dict[next(iter(table_dict))])):
        ins = CollectedData(
            country=table_dict['COUNTRY'][i],
            country_code=table_dict['COUNTRY CODE'][i],
            iso_codes=table_dict['ISO CODES'][i],
            population=table_dict['POPULATION'][i],
            area=table_dict['AREA KM'][i],
            gdp=table_dict['GDP $USD'][i],
        )
        session.add(ins)
        session.commit()
