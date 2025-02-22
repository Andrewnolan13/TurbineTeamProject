from .core import ForecastAPI, HistoricalAPI
from .enums import *
from .weather_variable_enums import *
from ..constants import SOURCE

import sqlite3

conn = sqlite3.connect(SOURCE.DATA.DB.str)
cursor = conn.cursor()


COMMAND = '''
CREATE TABLE IF NOT EXISTS hourly_historical_weather_data(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT,
    latitude REAL,
    longitude REAL,
    utc_offset_seconds INTEGER,
    timezone TEXT,
    timezone_abbreviation TEXT,
    elevation REAL,
    parameter TEXT,
    value REAL
);
'''

cursor.execute(COMMAND)
conn.commit()

COMMAND = '''
CREATE TABLE IF NOT EXISTS daily_historical_weather_data(
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT,
    latitude REAL,
    longitude REAL,
    utc_offset_seconds INTEGER,
    timezone TEXT,
    timezone_abbreviation TEXT,
    elevation REAL,
    parameter TEXT,
    value REAL
);
'''

cursor.execute(COMMAND)
conn.commit()

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS REQUESTS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL,
    call_weight REAL NOT NULL,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

cursor.execute(CREATE_TABLE)
conn.commit()
conn.close()
del conn, cursor, CREATE_TABLE