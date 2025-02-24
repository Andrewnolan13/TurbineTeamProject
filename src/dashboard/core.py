import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import datetime as dt

import pandas as pd
import sqlite3

from .utils import map_of_Ireland, plot_real_time_predictions, scatterPlotPower
from ..constants import SOURCE

# Placeholder function for getting data
def get_data():
    conn = sqlite3.connect(SOURCE.DATA.DB.str)
    df = pd.read_sql_query("SELECT * FROM real_time_predictions", conn)
    return df

initialDataFrame = get_data()
variables = initialDataFrame.columns.drop('Timestamps PowerPrediction'.split()).to_list()

app = dash.Dash(__name__)
app.layout = html.Div([
    html.Div(id = 'title',children='Real-time Wind Turbine Forecasting Dashboard',style={'textAlign':'center','fontSize':40}),
    html.Div(id = 'last-update-time',children = f'Last Updated: {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',style={'textAlign':'center','fontSize':20}),
    html.Div(style = {'display':'flex','height':'1000px', },
            children = [
                            html.Div(
                                style = {'border': '2px solid black', 'padding': '10px', 'margin-bottom': '20px','height':'100%','width':'100%'},
                                children  = dcc.Graph(id='predictionMap', figure=plot_real_time_predictions(initialDataFrame.copy()),config={'displayModeBar': False},style={'height':'100%', 'width':'100%'}), 
                            ),
                            html.Div(style = {'display':'flex','flexDirection':'column','width':'100%','height':'100%','border': '2px solid black', 'padding': '10px', 'margin-bottom': '20px'},
                                    children = [
                                                    dcc.Dropdown(
                                                        id='variable-dropdown',
                                                        options=[{'label': i, 'value': i} for i in variables],
                                                        value=variables[0],
                                                    ),
                                                    dcc.Graph(id='scatterPlot', figure=scatterPlotPower(initialDataFrame.copy(),variable = variables[0]),config={'displayModeBar': False},style={'height':'100%', 'width':'100%'}), 
                                    ]),
            ]),    
    dcc.Interval(
        id='interval-component',
        interval=1000,  # Update every second
        n_intervals=0
    )
])

@app.callback(
    [
        Output('last-update-time', 'children'),
        Output('predictionMap', 'figure'),
        Output('scatterPlot', 'figure'),
    ],
    [
        Input('interval-component', 'n_intervals'),
        Input('variable-dropdown', 'value')
    ]
)
def alwaysUpdatingComponents(n:int,variable:str):
    df = get_data()
    realtimePlot = plot_real_time_predictions(df)
    scatterPlot = scatterPlotPower(df,variable)
    timeStamp = "Last updated: {}".format(dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return (timeStamp,
            realtimePlot,
            scatterPlot
        )

