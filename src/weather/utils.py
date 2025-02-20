
from datetime import datetime
from typing import List, Dict, Any
import urllib.parse

class ApiCounter:
    """
    This is copied and translated from

    https://github.com/open-meteo/open-meteo-website/blob/main/src/lib/components/highcharts/ResultPreview.svelte

    params: This is expected to be a dictionary containing:
        time_mode: A string (e.g., "forecast_days", "time_interval").
        forecast_days: An integer or float (e.g., 7).
        past_days: An integer or float (e.g., 0).
        start_date and end_date: Strings representing ISO 8601 date/time formats (e.g., "2025-02-20T00:00:00").
        models: A list of strings representing model names (e.g., ["icon_seamless", "gfs025"]).
        hourly, daily, current, minutely_15: Lists of variables.
        lat: A list (could contain coordinates or just a single value).
    sdk_type: (str), "ensemble_api" or some other value that determines how the models are handled in the calculation.

    ```
    let callWeight = $derived(
        ((params) => {
            function membersPerModel(model: string): number {
                switch (model) {
                    case 'icon_seamless':
                        return 40;
                    case 'icon_global':
                        return 40;
                    case 'icon_eu':
                        return 40;
                    case 'icon_d2':
                        return 20;
                    case 'gfs_seamless':
                        return 31;
                    case 'gfs025':
                        return 31;
                    case 'gfs025':
                        return 31;
                    case 'ecmwf_ifs04':
                        return 51;
                    case 'gem_global':
                        return 21;
                }
                return 1;
            }
            let nDays = 1;
            if ('start_date' in params) {
                const start = new Date(params['start_date']).getTime();
                const end = new Date(params['end_date']).getTime();
                nDays = (end - start) / 1000 / 86400;
            } else {
                const forecast_days = params['forecast_days'] ?? 7;
                const past_days = params['past_days'] ?? 0;
                nDays = Number(forecast_days) + Number(past_days);
            }
            /// Number or models (including number of ensemble members)
            const nModels =
                sdk_type == 'ensemble_api'
                    ? ('models' in params
                            ? Array.isArray(params['models'])
                                ? params['models']
                                : [params['models']]
                            : []
                        ).reduce((previous: number, model: string) => {
                            return previous + (membersPerModel(model) ?? 1);
                        }, 0)
                    : ('models' in params
                            ? Array.isArray(params['models'])
                                ? params['models']
                                : [params['models']]
                            : []
                        ).length;

            /// Number of weather variables for hourly, daily, current or minutely_15
            const nHourly =
                'hourly' in params
                    ? Array.isArray(params['hourly'])
                        ? params['hourly'].length
                        : params['hourly'].length > 1
                            ? 1
                            : 0
                    : 0;
            const nDaily =
                'daily' in params
                    ? Array.isArray(params['daily'])
                        ? params['daily'].length
                        : params['daily'].length > 1
                            ? 1
                            : 0
                    : 0;
            const nCurrent =
                'current' in params
                    ? Array.isArray(params['current'])
                        ? params['current'].length
                        : params['current'].length > 1
                            ? 1
                            : 0
                    : 0;
            const nMinutely15 =
                'minutely_15' in params
                    ? Array.isArray(params['minutely_15'])
                        ? params['minutely_15'].length
                        : params['minutely_15'].length > 1
                            ? 1
                            : 0
                    : 0;
            const nVariables = nHourly + nDaily + nCurrent + nMinutely15;

            /// Number of locations
            const nLocations = params['latitude']?.length ?? 1.0;

            /// Calculate adjusted weight
            const nVariablesModels = nVariables * Math.max(nModels, 1.0);
            const timeWeight = nDays / 14.0;
            const variablesWeight = nVariablesModels / 10.0;
            const variableTimeWeight = Math.max(variablesWeight, timeWeight * variablesWeight);
            return Math.max(1.0, variableTimeWeight) * nLocations;
        })(parsedParams)
    );
    ```        
    """
    @staticmethod
    def members_per_model(model: str) -> int:
        model_weights = {
            'icon_seamless': 40,
            'icon_global': 40,
            'icon_eu': 40,
            'icon_d2': 20,
            'gfs_seamless': 31,
            'gfs025': 31,
            'ecmwf_ifs04': 51,
            'gem_global': 21
        }
        return model_weights.get(model, 1)

    @staticmethod
    def calculate_call_weight(params: Dict[str, Any], sdk_type: str) -> float:
        n_days = 1
        if 'start_date' in params:
            start_date = datetime.strptime(params['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(params['end_date'], '%Y-%m-%d')
            n_days = (end_date - start_date).days
        else:
            forecast_days = params.get('forecast_days', 7)
            past_days = params.get('past_days', 0)
            n_days = forecast_days + past_days

        # Number of models (including number of ensemble members)
        n_models = 0
        if sdk_type == 'ensemble_api':
            models = params.get('models', [])
            if isinstance(models, list):
                n_models = sum(ApiCounter.members_per_model(model) for model in models)
            elif isinstance(models, str):
                n_models = ApiCounter.members_per_model(models)
        else:
            models = params.get('models', [])
            if isinstance(models, list):
                n_models = len(models)
            elif isinstance(models, str):
                n_models = 1

        # Number of weather variables for hourly, daily, current or minutely_15
        n_variables = 0
        for time_period in ['hourly', 'daily', 'current', 'minutely_15']:
            if time_period in params:
                if isinstance(params[time_period], list):
                    n_variables += len(params[time_period])
                elif isinstance(params[time_period], str) and len(params[time_period]) > 1:
                    n_variables += 1

        # Number of locations
        n_locations = len(params.get('latitude', [1.0]))

        # Calculate adjusted weight
        n_variables_models = n_variables * max(n_models, 1.0)
        time_weight = n_days / 14.0
        variables_weight = n_variables_models / 10.0
        variable_time_weight = max(variables_weight, time_weight * variables_weight)
        
        return max(1.0, variable_time_weight) * n_locations
    
    @staticmethod
    def parse_url_params(url: str) -> Dict:
        parsed_url = urllib.parse.urlparse(url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        params = {}

        # Extract forecast days
        if 'forecast_days' in query_params:
            params['forecast_days'] = int(query_params['forecast_days'][0])

        # Extract start and end date (assuming the start_date and end_date are passed as 'start_date' and 'end_date')
        if 'start_date' in query_params and 'end_date' in query_params:
            params['start_date'] = query_params['start_date'][0]
            params['end_date'] = query_params['end_date'][0]

        # Extract models (e.g., 'models' param is not directly in the URL but could be inferred from query)
        # If models are present in the URL in any way, you can add them here.

        # Extract weather variables for hourly, daily, and current
        if 'current' in query_params:
            params['current'] = query_params['current'][0].split(',')
        if 'hourly' in query_params:
            params['hourly'] = query_params['hourly'][0].split(',')
        if 'daily' in query_params:
            params['daily'] = query_params['daily'][0].split(',')

        # Latitude and Longitude (if present)
        if 'latitude' in query_params:
            params['latitude'] = [float(lat) for lat in query_params['latitude']]
        if 'longitude' in query_params:
            params['longitude'] = [float(lon) for lon in query_params['longitude']]

        return params

    @staticmethod
    def calculate_call_weight_from_url(url: str, sdk_type: str='weather_api') -> float:
        params = ApiCounter.parse_url_params(url)
        return ApiCounter.calculate_call_weight(params, sdk_type)

import  sqlite3
from ..constants import RATE_LIMITS 

# Why is everything a class? Because Java has done this to me.

class RequestLogger:
    '''
    simple class to read and write to the REQUESTS table in the database.

    what does it do?
        * Keeps track of the number of requests made per call, with a timestamp, will show url too for debug. 
        * It will also be used to throw an error if there have been too many requests made. This is because I don't want to get blocked from open-meteo.

    functionality:
        It will be used in the api classes defined in abstract_classes.py.
        It will be asked to log every time a request is made.
        It will be asked for the number of requests left until the top of the current minute, hour and day. There are seperate agg rate limits deined in open-meteos docs.
        It will need a connection to the database. As will the api classes.

        I don't think this will have a specific dependency on speed, so it's probably fine to just create a new connection every time.
        If I do prefer not to create the connection everytime, I could pass the connection to the WeatherAPI class and allow it to manage the connection ie reconnect every five minutes.
    
        actually if that's the case then, I can probably just make this a static class.
    '''

    #make timestamp automatic. I want YYYY-MM-DD HH:MM:SS
    CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS REQUESTS (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        call_weight REAL NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """
    @staticmethod
    def __create_table(conn:sqlite3.Connection)->None:
        cursor = conn.cursor()
        cursor.execute(RequestLogger.CREATE_TABLE)
        conn.commit()
    
    @staticmethod
    def queryRemaining(conn:sqlite3.Connection)->dict[str,float]:
        '''
        query the database for the number of requests made in the last minute, hour and day.
        '''
        RequestLogger.__create_table(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(call_weight) FROM REQUESTS WHERE timestamp > datetime('now','-60 seconds')")
        minute = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(call_weight) FROM REQUESTS WHERE timestamp > datetime('now','-1 hour')")
        hour = cursor.fetchone()[0]
        cursor.execute("SELECT SUM(call_weight) FROM REQUESTS WHERE timestamp > datetime('now','-1 day')")
        day = cursor.fetchone()[0]

        daily_remaining = RATE_LIMITS.DAILY.value - (day if day is not None else 0)
        hourly_remaining = RATE_LIMITS.HOURLY.value - (hour if hour is not None else 0)
        minutely_remaining = RATE_LIMITS.MINUTE.value - (minute if minute is not None else 0)

        return dict(daily=daily_remaining,hourly=hourly_remaining,minutely=minutely_remaining)

    @staticmethod
    def log_request(conn:sqlite3.Connection,url:str,call_weight:float)->None:
        '''
        log the request in the database.
        '''
        RequestLogger.__create_table(conn)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO REQUESTS (url,call_weight) VALUES (?,?)",(url,call_weight))
        conn.commit()

if __name__ == '__main__':
    # Example usage
    # params = {
    #     "start_date": "2020-02-01",
    #     "end_date": "2025-02-07",
    #     "models": ["gfs_seamless", "icon_global"],
    #     "hourly": ["temperature_2m", "precipitation"],
    #     "latitude": [40.7128],
    #     "longitude": [-74.0060]
    # }

    # sdk_type = "weather_api"

    # call_weight = calculate_call_weight(params, sdk_type)
    # print(f"Adjusted API call weight: {call_weight}")


    # all these test cases agree with the website.
    url = "https://open-meteo.com/en/docs#current=precipitation,rain,showers,snowfall&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,snow_depth,visibility,et0_fao_evapotranspiration,vapour_pressure_deficit&daily=wind_speed_10m_max,wind_gusts_10m_max&forecast_days=16"        
    url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=precipitation,rain,showers,snowfall&hourly=temperature_2m,relative_humidity_2m,dew_point_2m,apparent_temperature,precipitation_probability,precipitation,rain,showers,snowfall,snow_depth,visibility,et0_fao_evapotranspiration,vapour_pressure_deficit&daily=wind_speed_10m_max,wind_gusts_10m_max&forecast_days=16"
    url = "https://archive-api.open-meteo.com/v1/archive?latitude=52.52&longitude=13.41&start_date=2025-01-01&end_date=2025-02-20&hourly=temperature_2m,relative_humidity_2m,dew_point_2m"
    url = 'https://archive-api.open-meteo.com/v1/archive?latitude=52.52&longitude=13.41&start_date=2025-01-01&end_date=2025-02-20&hourly=temperature_2m,relative_humidity_2m,dew_point_2m&daily=weather_code,temperature_2m_max&timezone=GMT'
    call_weight = ApiCounter.calculate_call_weight_from_url(url)
    print(f"Adjusted API call weight: {call_weight}")