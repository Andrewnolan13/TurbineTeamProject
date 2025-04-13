'''
run this file to create and fill up the database with the necessary data for the dashboard to run.
'''

from src import WindSpeedUnit, ForecastAPI, ForecastCurrent, HistoricalAPI, HistoricalDaily, HistoricalHourly
import src
import pandas as pd
import datetime as dt

f = HistoricalAPI()
f.latitude, f.longitude = src.GEO_COORDINATES.DUNDALK_IT.value
f.wind_speed_unit = WindSpeedUnit.METERS_PER_SECOND
f.hourly = [HistoricalHourly.TEMPERATURE_2M, HistoricalHourly.WIND_SPEED_100M, HistoricalHourly.WIND_DIRECTION_100M]
f.start_date = dt.datetime(2022, 10, 12)
f.end_date = dt.datetime(2022, 12, 31)
f.cell_selection = src.enums.CellSelection.NEAREST

response = f.request()
print(f.build_url())
