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

from abc import ABC, abstractmethod
from ..utils import enforce_types
from . import weather_variable_enums
from . import enums
import datetime as dt

class OpenMeteoAPI(ABC):
    @enforce_types
    def __init__(self,base_url:str):
        self.base_url:str = base_url

        # Parameters
        self._latitude:float|None = None #required
        self._longitude:float|None = None #required
        self._elevation:float|None = None
        self._hourly:str|None = None # must come from weather_variable_enums
        self._daily:str|None = None  # must come from weather_variable_enums
        self._temperature_unit:enums.TemperatureUnit|None = None
        self._wind_speed_unit:enums.WindSpeedUnit|None = None
        self._precipitation_unit:enums.PrecipitationUnit|None = None
        self._timeformat:enums.TimeFormat|None = None
        self._timezone:enums.TimeZone|None = None
        self._start_date:dt.datetime|None = None
        self._end_date:dt.datetime|None = None
        self._cell_selection:enums.CellSelection|None = None
        self._apikey:str|None = None

    # not allowed to be none.
    @property
    def latitude(self)->float|None:
        if self._latitude is None:
            raise NotImplementedError("latitude is None, it must be manually set before use")
        return self._latitude
    
    @latitude.setter
    @enforce_types
    def latitude(self,value:float):
        self._latitude = value
    
    @property
    def longitude(self)->float|None:
        if self._longitude is None:
            raise NotImplementedError("longitude is None, it must be manually set before use")
        return self._longitude
    
    @longitude.setter
    @enforce_types
    def longitude(self,value:float):
        self._longitude = value

    # optionals
    @property
    def elevation(self)->float|None:
        return self._elevation
    
    @elevation.setter
    @enforce_types
    def elevation(self,value:float|None):
        self._elevation = value

    @property
    def temperature_unit(self)->str|None:
        return self._temperature_unit.value if self._temperature_unit is not None else None
    
    @temperature_unit.setter
    @enforce_types
    def temperature_unit(self,value:enums.TemperatureUnit|None):
        self._temperature_unit = value

    @property
    def wind_speed_unit(self)->str|None:
        return self._wind_speed_unit.value if self._wind_speed_unit is not None else None

    @wind_speed_unit.setter
    @enforce_types
    def wind_speed_unit(self,value:enums.WindSpeedUnit|None):
        self._wind_speed_unit = value

    @property
    def precipitation_unit(self)->str|None:
        return self._precipitation_unit.value if self._precipitation_unit is not None else None

    @precipitation_unit.setter
    @enforce_types
    def precipitation_unit(self,value:enums.PrecipitationUnit|None):
        self._precipitation_unit = value

    @property
    def timeformat(self)->str|None:
        return self._timeformat.value if self._timeformat is not None else None
    
    @timeformat.setter
    @enforce_types
    def timeformat(self,value:enums.TimeFormat|None):
        self._timeformat = value

    @property
    def timezone(self)->str|None:
        return self._timezone.value if self._timezone is not None else None

    @timezone.setter
    @enforce_types
    def timezone(self,value:enums.TimeZone|None):
        self._timezone = value
    
    @property
    def start_date(self)->str|None:
        return self._start_date.strftime('%Y-%m-%d') if self._start_date is not None else None
    
    @start_date.setter
    @enforce_types
    def start_date(self,value:dt.datetime|None):
        self._start_date = value

    @property
    def end_date(self)->dt.datetime|None:
        return self._end_date.strftime('%Y-%m-%d') if self._end_date is not None else None
    
    @end_date.setter
    @enforce_types
    def end_date(self,value:dt.datetime|None):
        self._end_date = value

    @property
    def cell_selection(self)->str|None:
        return self._cell_selection.value if self._cell_selection is not None else None
    
    @cell_selection.setter
    @enforce_types
    def cell_selection(self,value:enums.CellSelection|None):
        self._cell_selection = value

    @property
    def apikey(self)->str|None:
        return self._apikey
    
    @apikey.setter
    @enforce_types
    def apikey(self,value:str|None):
        self._apikey = value
    




    



















    


class ForecastAPI(OpenMeteoAPI):
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
    @enforce_types
    def __init__(self):
        super().__init__('https://api.open-meteo.com/v1/forecast')
        self._start_hour = None
        self._end_hour = None
        self._start_minutely_15 = None
        self._end_minutely_15 = None
        self._models = None
        self._current = None
        self._minutely_15 = None
        self._past_days = None
        self._forecast_days = None
        self._forecast_hours = None
        self._forecast_minutely_15 = None
        self._past_hours = None
        self._past_minutely_15 = None                

class HistoricalAPI(OpenMeteoAPI):
    @enforce_types
    def __init__(self):
        super().__init__('https://archive-api.open-meteo.com/v1/archive')
