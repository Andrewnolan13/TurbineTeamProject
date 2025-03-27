from plotly import express as px
from plotly.graph_objects import Figure
import pandas as pd
pd.options.plotting.backend = "plotly"


def map_of_Ireland(df:pd.DataFrame)->px.scatter_mapbox:
    fig = px.scatter_mapbox(df, lat='latitude', lon='longitude',
                            color='temperature', size_max=10,
                            color_continuous_scale='plasma',
                            zoom=6, mapbox_style='open-street-map')
    # fig.update_layout(width = 800, height = 800)
    return fig.update_layout(uirevision='None')

def plot_real_time_predictions(df:pd.DataFrame)->px.line:
    return(
            df.melt(id_vars = 'Timestamps',)            
            .sort_values('Timestamps variable'.split(),ignore_index=True)
            .plot(x = 'Timestamps', y = 'value', color = 'variable', title = 'Real Time Predictions for Dundalk IT')
            .update_traces(selector = dict(name = 'WindDirAbs'), line = dict(width = 1,color = 'orange'))
            .update_traces(selector = dict(name = 'PowerPrediction'), line = dict(width = 4,color = 'red'))
            .update_layout(yaxis2 = dict(side = 'right',overlaying = 'y') )
            .update_traces(selector = dict(name = 'EnvirTemp'), yaxis = 'y2', line = dict(width = 1,color = 'green'))
            .update_traces(selector = dict(name = 'WindSpeed'), yaxis = 'y2', line = dict(width = 1,color = 'blue'))            
            .update_layout(title_x = 0.5)
            .update_layout(uirevision='None')
        )

def scatterPlotPower(df:pd.DataFrame,variable:str)->px.scatter:
    return(
            df.plot(x = variable, y = 'PowerPrediction', title = 'Scatter Plot of Power Prediction vs ' + variable, kind = 'scatter')
            .update_traces(marker = dict(size = 5,color = 'blue'))
            .update_layout(title_x = 0.5)
            .update_layout(uirevision='None')
        )

from ..utils import parseArgs
from ..constants import SOURCE
import datetime as dt

from os.path import join

anomaly_df = pd.read_pickle(join(SOURCE.str,'FaultPrediction','anomaly_df.pkl'))
window = 1.1#parseArgs().predictionWindow
timedelta = dt.timedelta(days = int(window), hours = int((window - int(window))*24))
timedelta = pd.Timedelta(timedelta)

def getFaultPredictionData(start:pd.Timestamp=None)->pd.DataFrame:
    '''
    spoofed data until I figure out what way we are gunna do this.
    I don't think this reconstruction thing is gunna be able to forward extrapolate from a starting point.
    We prob need another lstm/arima to do it. 
    '''
    if start is None:
        start = anomaly_df.time_stamp.min()
    end = start + timedelta
    return anomaly_df.query('time_stamp >= @start and time_stamp <= @end')
    
def makeFaultPredictionViz(df:pd.DataFrame)->Figure:
    fig = df.plot(x = 'time_stamp', y = 'reconstruction_error')
    scatter = px.scatter(df, x='time_stamp', y='reconstruction_error', color='is_anomaly_local')

    fig.add_trace(scatter.data[0])
    fig.add_trace(scatter.data[1])
    return fig.update_layout(uirevision='None',title = 'Fault Prediction Visualization',title_x = 0.5)

from ..weather.core import HistoricalAPI
from ..weather.enums import WindSpeedUnit, TemperatureUnit, CellSelection
from ..weather.weather_variable_enums import HistoricalHourly
from ..weather.utils import RequestLogger
from ..constants import SOURCE, GEO_COORDINATES
from ..models import FeedForwardNN
import torch
from sklearn.preprocessing import MinMaxScaler
import sqlite3

# def getHistoricalPowerPredictions(start:pd.Timestamp=None)->pd.DataFrame:
#     if start is None:
#         start = anomaly_df.time_stamp.min()
#     end = start + timedelta

class _getHistoricalPowerPredictions:
    '''callable class because I only wanna make the api connection once'''
    def __init__(self):
        self.__numCalls = 0
        self.api = None

    def __call__(self, start:pd.Timestamp=None)->pd.DataFrame:
        if self.__numCalls == 0:
            self.connect()         
            self.__numCalls += 1

        if start is None:
            start = anomaly_df.time_stamp.min()
        end = start + timedelta
        self.api.start_date = start.to_pydatetime()-dt.timedelta(days=1)
        self.api.end_date = end.to_pydatetime()+dt.timedelta(days=1)
        # make request
        try:
            response = self.api.request()
        except sqlite3.ProgrammingError as e:
            if 'SQLite objects created in a thread can only be used in that same thread' in str(e):
                self.connect()
                self.api.start_date = start.to_pydatetime()-dt.timedelta(days=1)
                self.api.end_date = end.to_pydatetime()+dt.timedelta(days=1)                
                response = self.api.request()
            else:
                raise e
        # return df with predictions
        return self.__predict(self.__formatJsonToDataFrame(response,start,end))
    
    def connect(self):
        # if self.api is not None:
        #     self.api._conn.close()
        # setup api
        api = HistoricalAPI()
        api.latitude, api.longitude = GEO_COORDINATES.DUNDALK_IT.value
        api.wind_speed_unit = WindSpeedUnit.METERS_PER_SECOND
        api.hourly = [HistoricalHourly.WIND_SPEED_100M, HistoricalHourly.WIND_DIRECTION_100M, HistoricalHourly.TEMPERATURE_2M]
        api.cell_selection = CellSelection.NEAREST
        api.temperature_unit = TemperatureUnit.CELSIUS
        self.api = api

        # load NN
        self.model = FeedForwardNN(3)
        self.model.load_state_dict(torch.load(SOURCE.MODELS.FFNN.str))
        self.xScaler:MinMaxScaler = torch.load(SOURCE.MODELS.xScaler_ffnn.str,weights_only=False)
        self.yScaler:MinMaxScaler = torch.load(SOURCE.MODELS.yScaler_ffnn.str,weights_only=False)           

    @staticmethod
    def __formatJsonToDataFrame(response:dict,start:dt.datetime,end:dt.datetime)->pd.DataFrame:
        '''
        makes json into df
        '''
        return (
            pd.DataFrame(response[0]['hourly'])
                .rename(columns={'time': 'Timestamps', 'wind_speed_100m': 'WindSpeed', 'wind_direction_100m': 'WindDirAbs', 'temperature_2m': 'EnvirTemp'})
                .assign(Timestamps = lambda x: x.Timestamps.astype('str'),
                        WindSpeed = lambda x: x.WindSpeed.astype('float'),
                        WindDirAbs = lambda x: x.WindDirAbs.astype('float'),
                        EnvirTemp = lambda x: x.EnvirTemp.astype('float'))
                [['Timestamps', 'WindSpeed', 'WindDirAbs', 'EnvirTemp']]
                .loc[lambda x: x.Timestamps>=start.strftime('%Y-%m-%d %H:%M:%S')]
                .loc[lambda x: x.Timestamps<=end.strftime('%Y-%m-%d %H:%M:%S')]
        )

    def __predict(self,df:pd.DataFrame)->pd.DataFrame:
        x = self.xScaler.transform(df[['WindSpeed','WindDirAbs','EnvirTemp']])
        x = torch.tensor(x).float()
        y = self.model(x)
        y = self.yScaler.inverse_transform(y.detach().numpy())
        return df.assign(PowerPrediction = y)
    
getHistoricalPowerPredictions = _getHistoricalPowerPredictions()