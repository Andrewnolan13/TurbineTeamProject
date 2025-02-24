from .weather.core import ForecastAPI
from .weather.enums import WindSpeedUnit, TemperatureUnit, CellSelection
from .weather.weather_variable_enums import ForecastMinutely15
from .weather.utils import RequestLogger
from .constants import SOURCE, GEO_COORDINATES
from .models import FeedForwardNN
from .utils import secondsTillEndOf, parseArgs

import sqlite3
import threading
import torch
import datetime as dt
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
import time


'''
The code written here will entirely depend on the type of model being used. There's not much scope for abstraction  I think.
Will just be editing in place.
'''

class ForecastDaemon(threading.Thread):
    def __init__(self):
        # threading
        threading.Thread.__init__(self)
        self._stop_event = threading.Event()
        self._stop_event.clear()
        
        window = parseArgs().predictionWindow
        self.timedelta = dt.timedelta(days = int(window), hours = int((window - int(window))*24))
    
    def _request(self)->pd.DataFrame:
        self.api.end_minutely_15 = dt.datetime.now() + self.timedelta
        self.api.start_minutely_15 = dt.datetime.now()

        response = self.api.request()

        df = pd.DataFrame(response['minutely_15'])
        df.rename(columns = {'time':'Timestamps','wind_speed_80m':'WindSpeed','wind_direction_80m':'WindDirAbs','temperature_2m':'EnvirTemp'}, inplace = True)
        df = df[['Timestamps','WindSpeed','WindDirAbs','EnvirTemp']]

        df['Timestamps'] = df['Timestamps'].astype('str')
        df['WindSpeed'] = df['WindSpeed'].astype('float')
        df['WindDirAbs'] = df['WindDirAbs'].astype('float')
        df['EnvirTemp'] = df['EnvirTemp'].astype('float')

        return df
    
    def _predict(self,df:pd.DataFrame)->pd.DataFrame:
        x = self.xScaler.transform(df[['WindSpeed','WindDirAbs','EnvirTemp']])
        x = torch.tensor(x).float()
        y = self.model(x)
        y = self.yScaler.inverse_transform(y.detach().numpy())
        return df.assign(PowerPrediction = y)
    
    def _write(self,df:pd.DataFrame):
        df.to_sql('real_time_predictions',self.conn,if_exists='replace',index=False)
    
    def run(self):
        # db
        self.conn = sqlite3.connect(SOURCE.DATA.DB.str)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.commit()

        # ML
        self.model = FeedForwardNN(3)
        self.model.load_state_dict(torch.load(SOURCE.MODELS.FFNN.str))
        self.xScaler:MinMaxScaler = torch.load(SOURCE.MODELS.xScaler_ffnn.str,weights_only=False)
        self.yScaler:MinMaxScaler = torch.load(SOURCE.MODELS.yScaler_ffnn.str,weights_only=False)
        
        # initialize the api
        f = ForecastAPI()
        f.latitude, f.longitude = GEO_COORDINATES.DUNDALK_IT.value
        f.wind_speed_unit = WindSpeedUnit.METERS_PER_SECOND
        f.minutely_15 = [ForecastMinutely15.WIND_SPEED_80M, ForecastMinutely15.WIND_DIRECTION_80M, ForecastMinutely15.TEMPERATURE_2M]
        f.cell_selection = CellSelection.NEAREST
        f.temperature_unit = TemperatureUnit.CELSIUS
        f.end_minutely_15 = dt.datetime.now() + dt.timedelta(days=10)
        f.start_minutely_15 = dt.datetime.now()
        f._conn.close()
        f._conn = self.conn
        self.api = f

        while not self._stop_event.is_set():
            df = self._request()
            df = self._predict(df)
            self._write(df)

            secondsRemaining = {k:secondsTillEndOf(k) for k in ['minutely','hourly','daily']}
            requestRemaining = RequestLogger.queryRemaining(self.conn)

            sleepTimes = {k:secondsRemaining[k]/requestRemaining[k] for k in ['minutely','hourly','daily']}
            sleepTime = max(sleepTimes.values())
            sleepTime = max(sleepTime,secondsTillEndOf('minutely'))
            time.sleep(sleepTime)
            print("sleeping for",sleepTime)

        self.conn.close()

    def stop(self):
        self._stop_event.set()
        self.join()
    


        
