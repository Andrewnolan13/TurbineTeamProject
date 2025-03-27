'''
main code will be written here to pull from the open-meteo api.

1. The dundalk data has wind speed, wind direction abs, wind direction relative, Environment Temperature. Which means I need to be able to pull those at a minimum.
2. I need to be able to pull historical data, and forecast data.
3. Before making requests to the server for historical data, check the local database to see if the data is already there.
4. Write historical data to the local database if not present.
5. Write forecast data to the local database?? It might be nice to have incase of hitting the api limit. The forecasts are obviously subject to change. Maybe just write it initially and then see at a later stage 
    if it's necessary to check for forecast updates. Maybe the api will have a variable inidicating when the forecast was last updated.
6. I need a way to check the api limit and if it's reached. 

request counting https://github.com/open-meteo/open-meteo/issues/464
fractional counting is used
'''

#forecast url
'''
    https://api.open-meteo.com/v1/forecast
        ?latitude=52.52 
        &longitude=13.41
        &current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,snowfall,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m
        &minutely_15=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation,rain,snowfall,snowfall_height,freezing_level_height,sunshine_duration,weather_code,wind_speed_10m,wind_speed_80m,wind_direction_10m,wind_direction_80m,wind_gusts_10m,visibility,cape,lightning_potential,is_day,shortwave_radiation,direct_radiation,diffuse_radiation,direct_normal_irradiance,global_tilted_irradiance,terrestrial_radiation,shortwave_radiation_instant,direct_radiation_instant,diffuse_radiation_instant,direct_normal_irradiance_instant,global_tilted_irradiance_instant,terrestrial_radiation_instant
        &hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,snow_depth,weather_code,pressure_msl,surface_pressure,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,visibility,evapotranspiration,et0_fao_evapotranspiration,vapour_pressure_deficit,wind_speed_10m,wind_speed_80m,wind_speed_120m,wind_speed_180m,wind_direction_10m,wind_direction_80m,wind_direction_120m,wind_direction_180m,wind_gusts_10m,temperature_80m,temperature_120m,temperature_180m,soil_temperature_0cm,soil_temperature_6cm,soil_temperature_18cm,soil_temperature_54cm,soil_moisture_0_to_1cm,soil_moisture_1_to_3cm,soil_moisture_3_to_9cm,soil_moisture_9_to_27cm,soil_moisture_27_to_81cm,uv_index,uv_index_clear_sky,is_day,sunshine_duration,wet_bulb_temperature_2m,total_column_integrated_water_vapour,cape,lifted_index,convective_inhibition,freezing_level_height,boundary_layer_height
        &daily=weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,sunrise,sunset,daylight_duration,sunshine_duration,uv_index_max,uv_index_clear_sky_max,precipitation_sum,rain_sum,showers_sum,snowfall_sum,precipitation_hours,precipitation_probability_max,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,shortwave_radiation_sum,et0_fao_evapotranspiration
        &wind_speed_unit=ms
        &timezone=auto
        &forecast_days=16
        &models=best_match
        &temperature_unit=fahrenheit
        &precipitation_unit=inch
        &timeformat=unixtime
'''
#historical url
'''
https://archive-api.open-meteo.com/v1/archive
    ?latitude=52.52
    &longitude=13.41
    &start_date=2000-02-17
    &end_date=2025-02-19
    &hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation,rain,snowfall,snow_depth,weather_code,pressure_msl,surface_pressure,cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high,et0_fao_evapotranspiration,vapour_pressure_deficit,wind_speed_10m,wind_speed_100m,wind_direction_10m,wind_direction_100m,wind_gusts_10m,soil_temperature_0_to_7cm,soil_temperature_7_to_28cm,soil_temperature_28_to_100cm,soil_temperature_100_to_255cm,soil_moisture_0_to_7cm,soil_moisture_7_to_28cm,soil_moisture_28_to_100cm,soil_moisture_100_to_255cm,boundary_layer_height,wet_bulb_temperature_2m,total_column_integrated_water_vapour,is_day,sunshine_duration,albedo,snow_depth_water_equivalent
    &daily=weather_code,temperature_2m_max,temperature_2m_min,temperature_2m_mean,apparent_temperature_max,apparent_temperature_min,apparent_temperature_mean,sunrise,sunset,daylight_duration,sunshine_duration,precipitation_sum,rain_sum,snowfall_sum,precipitation_hours,wind_speed_10m_max,wind_gusts_10m_max,wind_direction_10m_dominant,shortwave_radiation_sum,et0_fao_evapotranspiration
    &wind_speed_unit=ms
    &timezone=auto
'''
import datetime as dt
from beartype import beartype
import requests
from abc import ABC
import sqlite3

from ..constants import SOURCE
from .. import exceptions
from .utils import ApiCounter, RequestLogger #These two ensure I don't get my IP blocked 
from . import enums
from .weather_variable_enums import (ForecastHourly,
                                     ForecastDaily, 
                                     HistoricalHourly, 
                                     HistoricalDaily, 
                                     ForecastCurrent, 
                                     ForecastMinutely15)


# Making abstract classes to avoid all the ugly boiler plate in the main classes

class OpenMeteoAPI(ABC):
    @beartype
    def __init__(self,base_url:str):
        self.base_url:str = base_url
        self._conn:sqlite3.Connection = sqlite3.connect(SOURCE.DATA.DB.str)#TODO: think about re opening the connection every few minutes or something.
        cursor = self._conn.cursor()
        # enable WAL mode
        cursor.execute("PRAGMA journal_mode=WAL")
        self._conn.commit()

        # Parameters
        self._latitude:float|None = None #required
        self._longitude:float|None = None #required
        self._elevation:float|None = None
        self._hourly:None|list[ForecastHourly]|list[HistoricalHourly] = None # must come from weather_variable_enums
        self._daily:None|list[ForecastDaily]|list[HistoricalDaily] = None  # must come from weather_variable_enums
        self._temperature_unit:enums.TemperatureUnit|None = None
        self._wind_speed_unit:enums.WindSpeedUnit|None = None
        self._precipitation_unit:enums.PrecipitationUnit|None = None
        self._timeformat:enums.TimeFormat|None = None
        self._timezone:enums.TimeZone|None = None
        self._start_date:dt.datetime|None = None
        self._end_date:dt.datetime|None = None
        self._cell_selection:enums.CellSelection|None = None
        self._apikey:str|None = None
    
    def __del__(self):
        if self._conn is not None:
            self._conn.close()
    
    def _reConnect(self):
        #TODO: implement this somehow.
        self._conn.close()
        self._conn = sqlite3.connect(SOURCE.DATA.DB.str)
        cursor = self._conn.cursor()
        # enable WAL mode
        cursor.execute("PRAGMA journal_mode=WAL")
        self._conn.commit()

    def _request(self)->dict:
        #
        # Handle reconnection to the database here  
        #

        # build url. Check remaining calls.
        url:str = self.build_url()
        remaining = RequestLogger.queryRemaining(self._conn)
        call_weight:float = ApiCounter.calculate_call_weight_from_url(url)

        print(f"Remaining: {remaining}")
        if any([remaining['daily'] - call_weight<0, remaining['hourly'] - call_weight<0, remaining['minutely'] - call_weight<0]):
            raise exceptions.TooManyRequests("Too many requests")
        print(f"API counts: {call_weight}")

        # Log request
        RequestLogger.log_request(self._conn, url, call_weight)
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def build_url(self)->str:
        url:str = self.base_url+'?'
        for attr in dir(self):
            if not attr.startswith('_') and getattr(self, attr) is not None:
                if attr in ['build_url','base_url','request','request_from_database']:
                    continue
                if isinstance((val:=getattr(self, attr)), list):
                    url += attr + '=' + str(','.join(val)) + '&'
                else:
                    url += attr + '=' + str(val) + '&'
        return url[:-1]

    # not allowed to be none.
    @property
    def latitude(self)->float|None:
        if self._latitude is None:
            raise NotImplementedError("latitude is None, it must be manually set before use")
        return self._latitude
    
    @latitude.setter
    @beartype
    def latitude(self,value:float):
        self._latitude = value
    
    @property
    def longitude(self)->float|None:
        if self._longitude is None:
            raise NotImplementedError("longitude is None, it must be manually set before use")
        return self._longitude
    
    @longitude.setter
    @beartype
    def longitude(self,value:float):
        self._longitude = value

    # optionals
    @property
    def elevation(self)->float|None:
        return self._elevation
    
    @elevation.setter
    @beartype
    def elevation(self,value:float|None):
        self._elevation = value

    @property
    def temperature_unit(self)->str|None:
        return self._temperature_unit.value if self._temperature_unit is not None else None
    
    @temperature_unit.setter
    @beartype
    def temperature_unit(self,value:enums.TemperatureUnit|None):
        self._temperature_unit = value

    @property
    def wind_speed_unit(self)->str|None:
        return self._wind_speed_unit.value if self._wind_speed_unit is not None else None

    @wind_speed_unit.setter
    @beartype
    def wind_speed_unit(self,value:enums.WindSpeedUnit|None):
        self._wind_speed_unit = value

    @property
    def precipitation_unit(self)->str|None:
        return self._precipitation_unit.value if self._precipitation_unit is not None else None

    @precipitation_unit.setter
    @beartype
    def precipitation_unit(self,value:enums.PrecipitationUnit|None):
        self._precipitation_unit = value

    @property
    def timeformat(self)->str|None:
        return self._timeformat.value if self._timeformat is not None else None
    
    @timeformat.setter
    @beartype
    def timeformat(self,value:enums.TimeFormat|None):
        self._timeformat = value

    @property
    def timezone(self)->str|None:
        return self._timezone.value if self._timezone is not None else None

    @timezone.setter
    @beartype
    def timezone(self,value:enums.TimeZone|None):
        self._timezone = value

    @property
    def cell_selection(self)->str|None:
        return self._cell_selection.value if self._cell_selection is not None else None
    
    @cell_selection.setter
    @beartype
    def cell_selection(self,value:enums.CellSelection|None):
        self._cell_selection = value

    @property
    def apikey(self)->str|None:
        return self._apikey
    
    @apikey.setter
    @beartype
    def apikey(self,value:str|None):
        self._apikey = value
    
class AbstractForecastAPI(OpenMeteoAPI):
    '''
    latitude                :on request:required     
    longitude               :on request:required   
    current                 :on request:optional
    minutely_15             :on request:optional
    hourly                  :on request:optional  
    daily                   :on request:optional 
    wind_speed_unit         :on init
    timezone                :on init
    forecast_days           :on request:optional <- Server defaults to 7. only include if requesting time series, not current weather.
    models                  :on init  
    temperature_unit        :on init    
    precipitation_unit      :on init  
    timeformat              :on init  
    '''
    @beartype
    def __init__(self):
        super().__init__('https://api.open-meteo.com/v1/forecast')
        self._start_hour:dt.datetime|None = None
        self._end_hour:dt.datetime|None = None
        self._start_minutely_15:dt.datetime|None = None
        self._end_minutely_15:dt.datetime|None = None
        self._models:list[enums.Models]|None = None
        self._current:list[ForecastCurrent]|None = None
        self._minutely_15:list[ForecastMinutely15]|None = None
        self._past_days:int|None = None
        self._forecast_days:int|None = None
        self._forecast_hours:int|None = None
        self._forecast_minutely_15:int|None = None
        self._past_hours:int|None = None
        self._past_minutely_15:int|None = None

    @property
    def start_date(self)->str|None:
        return self._start_date.strftime('%Y-%m-%d') if self._start_date is not None else None
    
    @start_date.setter
    @beartype
    def start_date(self,value:dt.datetime|None):
        self._start_date = value

    @property
    def end_date(self)->dt.datetime|None:
        return self._end_date.strftime('%Y-%m-%d') if self._end_date is not None else None
    
    @end_date.setter
    @beartype
    def end_date(self,value:dt.datetime|None):
        self._end_date = value

    @property
    def hourly(self)->list[str]|None:
        return [_.value for _ in self._hourly] if self._hourly is not None else None
    
    @hourly.setter
    @beartype
    def hourly(self,value:list[ForecastHourly]|None):
        self._hourly = value

    @property
    def daily(self)->list[str]|None:
        return [_.value for _ in self._daily] if self._daily is not None else None
    
    @daily.setter
    @beartype
    def daily(self,value:list[ForecastDaily]|None):
        self._daily = value

    @property
    def current(self)->list[str]|None:
        return [_.value for _ in self._current] if self._current is not None else None
    
    @current.setter
    @beartype
    def current(self,value:list[ForecastCurrent]|None):
        self._current = value

    @property
    def minutely_15(self)->list[str]|None:
        return [_.value for _ in self._minutely_15] if self._minutely_15 is not None else None

    @minutely_15.setter
    @beartype
    def minutely_15(self,value:list[ForecastMinutely15]|None):
        self._minutely_15 = value

    @property
    def models(self)->list[str]|None:
        return [_.value for _ in self._models] if self._models is not None else None
    
    @models.setter
    @beartype
    def models(self,value:list[enums.Models]|None):
        self._models = value

    @property
    def start_hour(self)->str|None:
        return self._start_hour.strftime('%Y-%m-%dT%H:%M') if self._start_hour is not None else None
    
    @start_hour.setter
    @beartype
    def start_hour(self,value:dt.datetime|None):
        self._start_hour = value
    
    @property
    def end_hour(self)->str|None:
        return self._end_hour.strftime('%Y-%m-%dT%H:%M') if self._end_hour is not None else None
    
    @end_hour.setter
    @beartype
    def end_hour(self,value:dt.datetime|None):
        self._end_hour = value

    @property
    def start_minutely_15(self)->str|None:
        return self._start_minutely_15.strftime('%Y-%m-%dT%H:%M') if self._start_minutely_15 is not None else None
    
    @start_minutely_15.setter
    @beartype
    def start_minutely_15(self,value:dt.datetime|None):
        self._start_minutely_15 = value

    @property
    def end_minutely_15(self)->str|None:
        return self._end_minutely_15.strftime('%Y-%m-%dT%H:%M') if self._end_minutely_15 is not None else None
    
    @end_minutely_15.setter
    @beartype
    def end_minutely_15(self,value:dt.datetime|None):
        self._end_minutely_15 = value

    @property
    def past_days(self)->int|None:
        return self._past_days
    
    @past_days.setter
    @beartype
    def past_days(self,value:int|None):
        self._past_days = value

    @property
    def forecast_days(self)->int|None:
        return self._forecast_days
    
    @forecast_days.setter
    @beartype
    def forecast_days(self,value:int|None):
        self._forecast_days = value

    @property
    def forecast_hours(self)->int|None:
        return self._forecast_hours
    
    @forecast_hours.setter
    @beartype
    def forecast_hours(self,value:int|None):
        self._forecast_hours = value

    @property
    def forecast_minutely_15(self)->int|None:
        return self._forecast_minutely_15
    
    @forecast_minutely_15.setter
    @beartype
    def forecast_minutely_15(self,value:int|None):
        self._forecast_minutely_15 = value

    @property
    def past_hours(self)->int|None:
        return self._past_hours
    
    @past_hours.setter
    @beartype
    def past_hours(self,value:int|None):
        self._past_hours = value

    @property
    def past_minutely_15(self)->int|None:
        return self._past_minutely_15
    
    @past_minutely_15.setter
    @beartype
    def past_minutely_15(self,value:int|None):
        self._past_minutely_15 = value

                

class AbstractHistoricalAPI(OpenMeteoAPI):
    @beartype
    def __init__(self):
        super().__init__('https://archive-api.open-meteo.com/v1/archive')
    
    @property
    def hourly(self)->list[str]|None:
        return [_.value for _ in self._hourly] if self._hourly is not None else None
    
    @hourly.setter
    @beartype
    def hourly(self,value:list[HistoricalHourly]|None):
        self._hourly = value

    @property
    def daily(self)->list[str]|None:
        return [_.value for _ in self._daily] if self._daily is not None else None

    @daily.setter
    @beartype
    def daily(self,value:list[HistoricalDaily]|None):
        self._daily = value
    @property
    def start_date(self)->str|None:
        if self._start_date is None:
            raise NotImplementedError("start_date is None, it must be manually set before use")
        return self._start_date.strftime('%Y-%m-%d')
    
    @start_date.setter
    @beartype
    def start_date(self,value:dt.datetime|None):
        self._start_date = value

    @property
    def end_date(self)->str|None:
        if self._end_date is None:
            raise NotImplementedError("end_date is None, it must be manually set before use")
        return self._end_date.strftime('%Y-%m-%d')
    
    @end_date.setter
    @beartype
    def end_date(self,value:dt.datetime|None):
        self._end_date = value

