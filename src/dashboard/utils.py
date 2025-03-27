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
window = parseArgs().predictionWindow
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
    return anomaly_df[(anomaly_df.time_stamp >= start) & (anomaly_df.time_stamp <= end)]
    
def makeFaultPredictionViz(df:pd.DataFrame)->Figure:
    fig = anomaly_df.plot(x = 'time_stamp', y = 'reconstruction_error')
    scatter = px.scatter(anomaly_df, x='time_stamp', y='reconstruction_error', color='is_anomaly_local')

    fig.add_trace(scatter.data[0])
    fig.add_trace(scatter.data[1])
    return fig.update_layout(uirevision='None',title = 'Fault Prediction Visualization',title_x = 0.5)

from ..weather.core import HistoricalAPI
from ..weather.enums import WindSpeedUnit, TemperatureUnit, CellSelection
from ..weather.weather_variable_enums import HistoricalHourly
from ..weather.utils import RequestLogger
from ..constants import SOURCE, GEO_COORDINATES
from ..models import FeedForwardNN

def getHistoricalPowerPredictions(start:pd.Timestamp=None)->pd.DataFrame:
    if start is None:
        start = anomaly_df.time_stamp.min()
    end = start + timedelta

class _getHistoricalPowerPredictions:
    '''callable class because I only wanna make the api connection once'''
    def __init__(self):
        api = HistoricalAPI()
        api.latitude, api.longitude = GEO_COORDINATES.DUNDALK_IT.value
        api.wind_speed_unit = WindSpeedUnit.METERS_PER_SECOND
        api.hourly = [HistoricalHourly.WIND_SPEED_100M, HistoricalHourly.WIND_DIRECTION_100M, HistoricalHourly.TEMPERATURE_2M]
        api.cell_selection = CellSelection.NEAREST
        api.temperature_unit = TemperatureUnit.CELSIUS
        self.api = api

    def __call__(self, start:pd.Timestamp=None)->pd.DataFrame:
        if start is None:
            start = anomaly_df.time_stamp.min()
        end = start + timedelta
        self.api.start_date = start.to_pydatetime()
        self.api.end_date = end.to_pydatetime()
        
        response = self.api.request()
    
    def __formatJsonToDataFrame(response:dict)->pd.DataFrame:
        '''
        
        '''
        pass