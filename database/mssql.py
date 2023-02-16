import urllib
import warnings

import pandas as pd
import pyodbc
from decouple import config
from sqlalchemy import create_engine

warnings.filterwarnings("ignore")


class MSSQLDatabase(object):

    SERVER = config("MSSQL_SERVER", cast=str)
    DATABASE = config("MSSQL_DATABASE", cast=str)
    USERNAME = config("MSSQL_USERNAME", cast=str)
    PASSWORD = config("MSSQL_PASSWORD", cast=str)

    CNX_STRING = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};DATABASE={DATABASE};UID={USERNAME};PWD={PASSWORD}"
    )

    PARSED_CNX_URL = urllib.parse.quote_plus(CNX_STRING)

    def __init__(self):
        self.engine = create_engine(
            f"mssql+pyodbc:///?odbc_connect={self.PARSED_CNX_URL}"
        )
        self.cnx = pyodbc.connect(self.CNX_STRING)

    def select_table(self, table_name):
        return pd.read_sql(f"SELECT * FROM {table_name}", self.cnx)
