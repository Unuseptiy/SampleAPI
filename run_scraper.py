# scraper.py
import argparse
import requests
from bs4 import BeautifulSoup, element
from pyparsing import *
import pandas as pd
from tabulate import tabulate
from typing import List, Dict, Union

from database.db_init import CollectedData
from database.get_engine import Session


class Scrapper:
    """Class for work with scrapped data"""
    soup = None

    def __init__(self, url_obj):
        response = requests.get(url_obj)
        soup = BeautifulSoup(response.text, 'html.parser')
        Scrapper.soup = soup

    @staticmethod
    def get_title() -> List[str]:
        """Parses the BeautifulSoup object and returns the table fields"""
        quote = Scrapper.soup.find_all('th')
        title_word_parser = Word(alphas) + ZeroOrMore(' ') + ZeroOrMore(Word(alphas + '$'))
        titles_func = []
        for title_func in quote:
            titles_func.append(' '.join(title_word_parser.parseString(title_func.text).asList()))
        for i_func in [1] * 3:
            del titles_func[-i_func]
        return titles_func

    @staticmethod
    def get_data() -> element.ResultSet:
        """Parses the BeautifulSoup object and returns the table data"""
        # data – data from all tables with <tbody> tag
        data_obj = Scrapper.soup.find_all('tbody')
        return data_obj

    @staticmethod
    def get_parsed_data() -> Dict[str, list]:
        """Composes dict from scrapped table, where keys – table fields, values – table data"""
        titles = Scrapper.get_title()
        data = Scrapper.get_data()

        # initialization of table_dict – a dictionary whose keys are the names of table fields, values are lists of
        # values in the corresponding fields
        table_dict = {}
        for title in titles:
            table_dict[title] = []

        # table_dict filling
        i: int = 0
        for string in data[0].text.split(sep='\n'):
            index = i % 8 - 2
            if index != -2 and index != -1:
                table_dict[titles[index]].append(string)
            i += 1
        return table_dict


def str2bool(v: str) -> bool:
    """Converts the entered command-line argument to the required form, or returns an error"""
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


if __name__ == "__main__":
    url = 'https://countrycode.org'

    scrapper = Scrapper(url)

    data_dict = scrapper.get_parsed_data()
    df = pd.DataFrame(data=data_dict)

    # adding an argument to the command line parser
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry_run", type=str2bool, nargs='?', const=True, default=False, help="A flag describing "
                                                                                               "where the table was "
                                                                                               "saved: in the "
                                                                                               "database or printed "
                                                                                               "in the console")

    if parser.parse_args().dry_run:
        # if --dry_run True, then table prints to console
        print(tabulate(df, headers='keys', tablefmt='psql'))
    else:
        session = Session()

        data_about_countries = session.query(CollectedData).all()

        # checking whether the collected_data table is empty
        if data_about_countries:
            # deleting all records from the collected_data table
            session.query(CollectedData).delete(synchronize_session='fetch')
            session.commit()

        # adding records to collected_data table
        for i in range(len(data_dict[next(iter(data_dict))])):
            ins = CollectedData(
                country=data_dict['COUNTRY'][i],
                country_code=data_dict['COUNTRY CODE'][i],
                iso_codes=data_dict['ISO CODES'][i],
                population=data_dict['POPULATION'][i],
                area=data_dict['AREA KM'][i],
                gdp=data_dict['GDP $USD'][i],
            )
            session.add(ins)
            session.commit()
