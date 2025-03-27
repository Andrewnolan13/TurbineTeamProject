import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import datetime as dt

import pandas as pd
import sqlite3

from .utils import plot_real_time_predictions, scatterPlotPower, getFaultPredictionData, getHistoricalPowerPredictions, makeFaultPredictionViz
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
    dcc.Tabs(id="tabs", value="tab-1", children=[
        dcc.Tab(label="Real-Time Dashboard", value="tab-1"),
        dcc.Tab(label="Placeholder Tab", value="tab-2")
    ]),
    
    html.Div(id="tabs-content"),

    dcc.Interval(id="interval-tab-1", interval=1000, n_intervals=0, disabled=True),
    dcc.Interval(id="interval-tab-2", interval=1000, n_intervals=0, disabled=True)
])

# Enable only the interval for the active tab
@app.callback(
    [Output("interval-tab-1", "disabled"),
     Output("interval-tab-2", "disabled")],
    [Input("tabs", "value")]
)
def control_intervals(active_tab):
    return active_tab != "tab-1", active_tab != "tab-2"

# Update content for each tab
@app.callback(
    Output("tabs-content", "children"),
    [Input("tabs", "value")]
)
def update_tab_content(tab):
    if tab == "tab-1":
        print("Tab 1")
        df = get_data()
        return html.Div([
            html.Div(id='title', children='Real-time Wind Turbine Forecasting Dashboard', style={'textAlign': 'center', 'fontSize': 40}),
            html.Div(id='last-update-time', children=f'Last Updated: {dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', style={'textAlign': 'center', 'fontSize': 20}),
            html.Div(style={'display': 'flex', 'height': '1000px'},
                     children=[
                         html.Div(
                             style={'border': '2px solid black', 'padding': '10px', 'margin-bottom': '20px', 'height': '100%', 'width': '100%'},
                             children=dcc.Graph(id='predictionMap', figure=plot_real_time_predictions(df), config={'displayModeBar': False}, style={'height': '100%', 'width': '100%'}),
                         ),
                         html.Div(style={'display': 'flex', 'flexDirection': 'column', 'width': '100%', 'height': '100%', 'border': '2px solid black', 'padding': '10px', 'margin-bottom': '20px'},
                                  children=[
                                      dcc.Dropdown(
                                          id='variable-dropdown',
                                          options=[{'label': i, 'value': i} for i in variables],
                                          value=variables[0],
                                      ),
                                      dcc.Graph(id='scatterPlot', figure=scatterPlotPower(df, variable=variables[0]), config={'displayModeBar': False}, style={'height': '100%', 'width': '100%'}),
                                  ]),
                     ]),
        ])
    
    elif tab == "tab-2":
        print("Tab 2")
        faultPredictionData = getFaultPredictionData() #<- will be time series with reconstruction errors.
        powerPredictions = getHistoricalPowerPredictions()
        return html.Div([
            html.H2("COME UP WITH A TITLE", style={'textAlign': 'center'}),
            # dash_table.DataTable(df.to_dict("records"), [{"name": i, "id": i} for i in df.columns])
            html.Div(style={'display': 'flex', 'height': '1000px'},
                     children=[
                         html.Div(
                             style={'border': '2px solid black', 'padding': '10px', 'margin-bottom': '20px', 'height': '100%', 'width': '100%'},
                             children=dcc.Graph(id='historicalPowerPred', figure=plot_real_time_predictions(powerPredictions), config={'displayModeBar': False}, style={'height': '100%', 'width': '100%'}),
                         ),
                         html.Div(style={'display': 'flex', 'flexDirection': 'column', 'width': '100%', 'height': '100%', 'border': '2px solid black', 'padding': '10px', 'margin-bottom': '20px'},
                                  children=dcc.Graph(id='faultPredictions', figure=makeFaultPredictionViz(faultPredictionData) , config={'displayModeBar': False}, style={'height': '100%', 'width': '100%'}),
                                  ),                                  
                     ]),
            dcc.Slider(
                id='time-slider',
                min=0,
                max=300,  # Assuming sorted time index
                step=1,  # Each step corresponds to a 10-min interval
                marks={i: (faultPredictionData.time_stamp.min().to_pydatetime()+ dt.timedelta(minutes = 10)).strftime('%Y-%m-%d %H:%M') for i in range(0, 300,144)},  # Show labels every 24 hours
                value=[0, 300]
            ),
            dcc.Interval(
                id='slider-interval-component',
                interval=1000,  # 1 second per step
                n_intervals=0,
                disabled=True  # Start disabled
            ),
            html.Button("Play", id="play-button", n_clicks=0),            

        ])            

# Update real-time data only when on Tab 1
@app.callback(
    [Output('last-update-time', 'children'),
     Output('predictionMap', 'figure'),
     Output('scatterPlot', 'figure')],
    [Input('interval-tab-1', 'n_intervals'), Input('variable-dropdown', 'value')]
)
def updateRealTimePredictionsTab(n: int, variable: str):
    df = get_data()
    realtimePlot = plot_real_time_predictions(df)
    scatterPlot = scatterPlotPower(df, variable)
    timeStamp = f"Last updated: {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return timeStamp, realtimePlot, scatterPlot

@app.callback(
    Output('time-slider', 'value'),
    Output('interval-component', 'disabled'),
    Input('interval-component', 'n_intervals'),
    Input('play-button', 'n_clicks'),
    State('time-slider', 'value')
)
def play_slider(n_intervals, play_clicks, current_value):
    print(f"Play clicks: {play_clicks}")
    ctx = dash.callback_context
    if not ctx.triggered or ctx.triggered[0]['prop_id'].split('.')[0] == 'play-button':
        return current_value, not (play_clicks % 2)  # Toggle play/pause
    
    next_value = min(current_value + 1, 300)
    return next_value, False  # Keep playing until the end





