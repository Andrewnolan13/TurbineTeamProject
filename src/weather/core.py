'''
main code will be written here to pull from the open-meteo api.

1. The dundalk data has wind speed, wind direction abs, wind direction relative, Environment Temperature. Which means I need to be able to pull those at a minimum.
2. I need to be able to pull historical data, and forecast data.
3. Before making requests to the server for historical data, check the local database to see if the data is already there.
4. Write historical data to the local database if not present.
5. Write forecast data to the local database?? It might be nice to have incase of hitting the api limit. The forecasts are obviously subject to change. Maybe just write it initially and then see at a later stage 
    if it's necessary to check for forecast updates. Maybe the api will have a variable inidicating when the forecast was last updated.
6. I need a way to check the api limit and if it's reached. 
'''
from abc import ABC, abstractmethod