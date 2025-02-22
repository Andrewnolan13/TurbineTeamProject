import datetime as dt
import pandas as pd
from copy import deepcopy

from .utils import ApiCounter
from .abstract_classes import AbstractForecastAPI, AbstractHistoricalAPI
from .weather_variable_enums import HistoricalHourly, HistoricalDaily

EPSILON = 1E-12


'''
Here I will write logic to read/write from db. Special logic for requests etc.
'''
class ForecastAPI(AbstractForecastAPI):
    def __init__(self):
        super().__init__()
    def request(self):
        # special logic here
        return super()._request()
    

class HistoricalAPI(AbstractHistoricalAPI):
    def __init__(self):
        super().__init__()
    def request_from_database(self)->list[dict]:
        '''
        Making very long historical requests has problems:
        1. it depletes the API call weight very quickly.
        2. The sloution to 1. is to parse the request and check what already exists in the databse, return that along with a response from the api.
        3. The problem with 3. is that it takes AGES to check what data exists/doesn't exist in the database.

        This function is then meant for just requesting from the database directly. So only use it if you are sure that the data you are requesting is in the database.
        '''
        conn = self._conn
        url = self.build_url()
        parsedParams = ApiCounter.parse_url_params(url)
        startDate = dt.datetime.strptime(parsedParams['start_date'], '%Y-%m-%d')#.strftime('%Y-%m-%d %H:%M:%S')
        endDate = dt.datetime.strptime(parsedParams['end_date'], '%Y-%m-%d')#.strftime('%Y-%m-%d %H:%M:%S')
        parsedParams['start_date'] = startDate.strftime('%Y-%m-%d %H:%M:%S')
        parsedParams['end_date'] = endDate.strftime('%Y-%m-%d %H:%M:%S')

        hourly = pd.read_sql_query(f'''
                  SELECT * FROM hourly_historical_weather_data
                  WHERE time BETWEEN ? AND ?
                  AND {'1=0' if parsedParams.get('hourly') is None else 'parameter IN (' + ','.join("'"+str(x)+"'" for x in parsedParams['hourly']) + ')'}
                  AND latitude = ?
                  AND longitude = ?
                  ''', conn, params=[parsedParams['start_date'], parsedParams['end_date'], parsedParams['latitude'][0], parsedParams['longitude'][0]])
        
        daily = pd.read_sql_query(f'''
                    SELECT * FROM daily_historical_weather_data
                    WHERE time BETWEEN ? AND ?
                    AND {'1=0' if parsedParams.get('daily') is None else 'parameter IN (' + ','.join("'"+str(x)+"'" for x in parsedParams['daily']) + ')'}
                    AND latitude = ?
                    AND longitude = ?
                    ''', conn, params=[parsedParams['start_date'], parsedParams['end_date'], parsedParams['latitude'][0], parsedParams['longitude'][0]])
        responses = []
        responses += self._convertToDictResponse(hourly, 'hourly')
        responses += self._convertToDictResponse(daily, 'daily')
        return responses
                                  

    def request(self)->list[dict]:
        # build the url.
        # parse the url into something that can be turned into a SQL query <- can do using my url parser
        # query the data base.
            # if it exists, return it. function terminates here.
        # if it doesn't exist, request the data from the API
        # parse the response to database friendly format
        # write to the database
        # return the data
        url = self.build_url()
        parsedParams = ApiCounter.parse_url_params(url)
        startDate = dt.datetime.strptime(parsedParams['start_date'], '%Y-%m-%d')#.strftime('%Y-%m-%d %H:%M:%S')
        endDate = dt.datetime.strptime(parsedParams['end_date'], '%Y-%m-%d')#.strftime('%Y-%m-%d %H:%M:%S')
        parsedParams['start_date'] = startDate.strftime('%Y-%m-%d %H:%M:%S')
        parsedParams['end_date'] = endDate.strftime('%Y-%m-%d %H:%M:%S')

        queryDaily = pd.DataFrame(data = pd.date_range(start=startDate, end=endDate, freq='D'), columns=['time'])
        queryDaily = queryDaily.merge(pd.DataFrame(data = parsedParams.get('daily',[]),columns = ['parameter']), how='cross')
        queryDaily = queryDaily.merge(
            pd.DataFrame(dict(latitude = parsedParams['latitude'], longitude = parsedParams['longitude'])),
            how='cross')
        queryDaily.time = queryDaily.time.dt.strftime('%Y-%m-%d %H:%M:%S')


        queryHourly = pd.DataFrame(data = pd.date_range(start=startDate,end=endDate, freq='h'), columns=['time'])
        queryHourly = queryHourly.merge(pd.DataFrame(data = parsedParams.get('hourly',[]),columns = ['parameter']), how='cross')
        queryHourly = queryHourly.merge(
            pd.DataFrame(dict(latitude = parsedParams['latitude'], longitude = parsedParams['longitude'])),
            how='cross')
        queryHourly.time = queryHourly.time.dt.strftime('%Y-%m-%d %H:%M:%S')

        #ensure dtypes
        queryDaily['time'] = queryDaily['time'].astype('str')
        queryDaily['parameter'] = queryDaily['parameter'].astype('str')
        queryDaily['latitude'] = queryDaily['latitude'].astype('float')
        queryDaily['longitude'] = queryDaily['longitude'].astype('float')

        queryHourly['time'] = queryHourly['time'].astype('str')
        queryHourly['parameter'] = queryHourly['parameter'].astype('str')
        queryHourly['latitude'] = queryHourly['latitude'].astype('float')
        queryHourly['longitude'] = queryHourly['longitude'].astype('float')


        #insert data
        conn = self._conn
        conn.execute('DELETE FROM hourly_historical_weather_staging_table')
        conn.execute('DELETE FROM daily_historical_weather_staging_table')
        conn.commit()
        queryDaily.to_sql('daily_historical_weather_staging_table', conn, if_exists='append', index=False)
        queryHourly.to_sql('hourly_historical_weather_staging_table', conn, if_exists='append', index=False)
        # queryDaily.to_sql('daily_historical_weather_staging_table', conn, if_exists='replace', index=False) - this deletes my indices which makes everything slow af
        # queryHourly.to_sql('hourly_historical_weather_staging_table', conn, if_exists='replace', index=False)
        
        # re index tables.
        # conn.execute('REINDEX hourly_historical_weather_data;')
        # conn.execute('REINDEX daily_historical_weather_data;')
        # conn.execute('REINDEX hourly_historical_weather_staging_table;')
        # conn.execute('REINDEX daily_historical_weather_staging_table;')
        # conn.commit()

        # create a command that joins the staging table (request table) with the historical data and then pull it out
        dailySearchCommand = f'''
        SELECT
            COALESCE(DAILY.time, daily_historical_weather_staging_table.time) AS time,
            COALESCE(DAILY.parameter, daily_historical_weather_staging_table.parameter) AS parameter,
            COALESCE(DAILY.latitude, daily_historical_weather_staging_table.latitude) AS latitude,
            COALESCE(DAILY.longitude, daily_historical_weather_staging_table.longitude) AS longitude,
            DAILY.value
        FROM (
            SELECT time, parameter, latitude, longitude, value
            FROM daily_historical_weather_data
            WHERE time BETWEEN ? AND ?
            AND {'1=0' if parsedParams.get('daily') is None else 'parameter IN (' + ','.join("'"+str(x)+"'" for x in parsedParams['daily']) + ')'}
        ) AS DAILY
        RIGHT JOIN daily_historical_weather_staging_table
        ON daily_historical_weather_staging_table.time = DAILY.time
        AND daily_historical_weather_staging_table.parameter = DAILY.parameter
--        AND ABS(daily_historical_weather_staging_table.latitude - DAILY.latitude) < {EPSILON} -- may not be necessary
--        AND ABS(daily_historical_weather_staging_table.longitude - DAILY.longitude) < {EPSILON}
        AND daily_historical_weather_staging_table.latitude = DAILY.latitude
        AND daily_historical_weather_staging_table.longitude = DAILY.longitude
        '''


        hourlySearchCommand = f'''
        SELECT 
            COALESCE(HOURLY.time, hourly_historical_weather_staging_table.time) AS time,
            COALESCE(HOURLY.parameter, hourly_historical_weather_staging_table.parameter) AS parameter,
            COALESCE(HOURLY.latitude, hourly_historical_weather_staging_table.latitude) AS latitude,
            COALESCE(HOURLY.longitude, hourly_historical_weather_staging_table.longitude) AS longitude,
            HOURLY.value
        FROM (
            SELECT time, parameter, latitude, longitude, value
            FROM hourly_historical_weather_data
            WHERE time BETWEEN ? AND ?
            AND {'1=0' if parsedParams.get('hourly') is None else 'parameter IN (' + ','.join("'"+str(x)+"'" for x in parsedParams['hourly']) + ')'}
        ) AS HOURLY
        RIGHT JOIN hourly_historical_weather_staging_table
        ON hourly_historical_weather_staging_table.time = HOURLY.time
        AND hourly_historical_weather_staging_table.parameter = HOURLY.parameter
--        AND ABS(hourly_historical_weather_staging_table.latitude - HOURLY.latitude) < {EPSILON}
--        AND ABS(hourly_historical_weather_staging_table.longitude - HOURLY.longitude) < {EPSILON}
        AND hourly_historical_weather_staging_table.latitude = HOURLY.latitude
        AND hourly_historical_weather_staging_table.longitude = HOURLY.longitude
        '''

        responseDaily = pd.read_sql_query(dailySearchCommand, conn, params=[parsedParams['start_date'], parsedParams['end_date']])
        responseHourly = pd.read_sql_query(hourlySearchCommand, conn, params=[parsedParams['start_date'], parsedParams['end_date']])

        # drop data from staging tables
        conn.execute('DELETE FROM daily_historical_weather_staging_table')
        conn.execute('DELETE FROM hourly_historical_weather_staging_table')
        conn.commit()

        foundHourly = responseHourly.copy().loc[lambda s:s.value.notna()]
        foundDaily = responseDaily.copy().loc[lambda s:s.value.notna()]
        notFoundHourly = responseHourly.copy().loc[lambda s:s.value.isna()]
        notFoundDaily = responseDaily.copy().loc[lambda s:s.value.isna()]

        newSelfs = self._make_new_selfs(notFoundHourly, HistoricalHourly)
        newSelfs += self._make_new_selfs(notFoundDaily, HistoricalDaily)

        # make requests to api
        responses:list[dict] = []
        for newSelf in newSelfs:
            responses += [AbstractHistoricalAPI._request(newSelf)]
        
        # submit responses to db
        dailyResponses = [response for response in responses if 'daily' in response]
        hourlyResponses = [response for response in responses if 'hourly' in response]
        self._write_to_db(dailyResponses, 'daily')
        self._write_to_db(hourlyResponses, 'hourly')

        # drop duplicates from db #:MAYBE. Might take too long even on small requests.
        conn.execute('''
        DELETE FROM hourly_historical_weather_data
        WHERE ID NOT IN (
            SELECT MIN(ID) 
            FROM hourly_historical_weather_data 
            GROUP BY time, latitude, longitude, utc_offset_seconds, timezone, timezone_abbreviation, elevation, parameter, value
        );
        ''') 
        conn.execute('''
        DELETE FROM daily_historical_weather_data
        WHERE ID NOT IN (
            SELECT MIN(ID) 
            FROM daily_historical_weather_data 
            GROUP BY time, latitude, longitude, utc_offset_seconds, timezone, timezone_abbreviation, elevation, parameter, value
        );
        ''')
        conn.commit()

        # convert foundHourly and foundDaily to list of dicts
        responses += self._convertToDictResponse(foundHourly, 'hourly')
        responses += self._convertToDictResponse(foundDaily, 'daily')

        return responses

    def _make_new_selfs(self,dataframe:pd.DataFrame,type:HistoricalDaily|HistoricalHourly)->list['HistoricalAPI']:
        df = dataframe.copy()
        df = df.assign(geo = lambda s: s.latitude.astype('str') + ',' + s.longitude.astype('str'))
        df.sort_values(by = 'geo parameter time'.split(), inplace=True, ignore_index=True)
        df['timeObj'] = pd.to_datetime(df.time)
        df = df.groupby('geo timeObj'.split()).agg(parameter = ('parameter',','.join)).reset_index()
        df = df.groupby('geo parameter'.split()).agg(start_date = ('timeObj','min'), end_date = ('timeObj','max')).reset_index()
        df = df.groupby('parameter start_date end_date'.split()).agg(geo = ('geo',' '.join)).reset_index()

        res = []
        for idx,row in df.iterrows():
            for geo in row['geo'].split(' '):
                latitude, longitude = geo.split(',')
                sd = row['start_date'].to_pydatetime()
                ed = row['end_date'].to_pydatetime()
                params = [type._value2member_map_[value] for value in row['parameter'].split(',')]
                
                new = HistoricalAPI()
                new.latitude = float(latitude)
                new.longitude = float(longitude)
                new.start_date = sd
                new.end_date = ed
                if type == HistoricalHourly:
                    new.hourly = params
                elif type == HistoricalDaily:
                    new.daily = params
                else:
                    raise ValueError('Invalid type')
                res.append(new)
        return res
    
    def _write_to_db(self,responses:list[dict],type:str):
        dataFrames = []
        for result in responses:
            metadata = dict()
            response = deepcopy(result)

            for k,v in result.items():
                if not isinstance(v, (list,dict)):
                    metadata[k] = response.pop(k)

            df = pd.DataFrame(response[type])
            for k,v in metadata.items():
                if k == 'generationtime_ms':
                    continue
                df[k] = v
            df = df.melt(id_vars = 'time latitude longitude utc_offset_seconds timezone timezone_abbreviation elevation'.split(),var_name = 'parameter',value_name = 'value')
            dataFrames.append(df)
        
        if len(dataFrames) > 0:
            submission = pd.concat(dataFrames,ignore_index=True)
            # force the written entries to have the same geo coords as the request. this is because the response returns a different geo coord, which is the centre of a grid cell or something.
            submission.latitude = self.latitude
            submission.longitude = self.longitude
            # ensure dtype float. Some values (eg sunrise time) return timestamps which I'm not interested in building architechture to suuport.
            submission.value = pd.to_numeric(submission.value, errors='coerce')
            submission.value = submission.value.astype('float').fillna(-2_147_483_648.0) # having float('nan') values messes up my join.
            # ensure time is in the correct format
            submission['time'] = pd.to_datetime(submission['time'], format='%Y-%m-%dT%H:%M' if type == 'hourly' else '%Y-%m-%d').dt.strftime('%Y-%m-%d %H:%M:%S')
            submission.to_sql(f'{type}_historical_weather_data', self._conn, if_exists='append', index=False)

    def _convertToDictResponse(self,df:pd.DataFrame,type:str)->list[dict]:
        '''
        convert the dataframes to how the API would return them.

        Example:
        {
            'latitude': 53.954304,
            'longitude': -6.4410095,
            'generationtime_ms': 0.07987022399902344,
            'utc_offset_seconds': 0,
            'timezone': 'GMT',
            'timezone_abbreviation': 'GMT',
            'elevation': 15.0,
            'daily_units': {'time': 'iso8601',
            'temperature_2m_mean': '°C',
            'wind_speed_10m_max': 'km/h'},
            'daily': {
                        'time': ['2020-01-01', '2020-01-02'],
                        'temperature_2m_mean': [5.3, 9.5],
                        'wind_speed_10m_max': [13.7, 26.1]
                        },
            'hourly_units': {
                            'time': 'iso8601',
                            'temperature_2m': '°C',
                            'wind_speed_10m': 'km/h'
                            },
            'hourly': {
                        'time': ['2020-01-01T00:00:00', '2020-01-01T01:00:00'],
                        'temperature_2m': [5.3, 5.2],
                        'wind_speed_10m': [13.7, 13.9]
                        }
        }

        I don't need:
        - daily_units
        - hourly_units
        '''
        gdf = df.copy()
        gdf = gdf.assign(geo = lambda s: s.latitude.astype('str') + ',' + s.longitude.astype('str'))
        res = (
            gdf.groupby('geo'.split())
                .agg(
                        latitude = ('latitude','first'), 
                        longitude = ('longitude','first'),
                    )
                .assign(
                        generationtime_ms = -10.0,
                        utc_offset_seconds= -10,
                        timezone= 'GMT',
                        timezone_abbreviation= 'GMT',
                        elevation= -9999,
                        daily_units= lambda df:df.shape[0]*[{'time': 'iso8601','temperature_2m_mean': '°C','wind_speed_10m_max': 'km/h'}],            
                )
                .rename(columns = dict(daily_units=f'{type}_units'))
                .reset_index(drop=True)
                .to_dict(orient='records')
        )
        # this was slowing the function down alot.
        # gdf.time = pd.to_datetime(gdf.time).dt.strftime('%Y-%m-%dT%H:%M:%S') #format='%Y-%m-%dT%H:%M' if type == 'hourly' else '%Y-%m-%d'
        for dict_,(_,grp) in zip(res,gdf.groupby('geo')):
            dict_[type] = grp.pivot_table(index = 'time', columns = 'parameter', values = 'value', aggfunc='first').reset_index().to_dict(orient='list')
        
        return res
        