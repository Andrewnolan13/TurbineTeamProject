import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import time
import numpy as np

from .utils import map_of_Ireland

# Placeholder function for getting data
def get_data():
    return pd.DataFrame({
        'latitude': [53.3498, 52.668, 54.5973],  # Example locations
        'longitude': [-6.2603, -8.6305, -5.9301],
        'temperature': np.random.randint(0, 30, 3)  # Example temperature
    })

initialDataFrame = get_data()

app = dash.Dash(__name__)
app.layout = html.Div([
    html.Div(id = 'title',children='Real-time Wind Turbine Forecasting Dashboard',style={'textAlign':'center','fontSize':40}),
    html.Div(
        dcc.Graph(id='weatherMap', figure=map_of_Ireland(initialDataFrame.copy()),config={'displayModeBar': False},style={'height':'100%', 'width':'100%'}), 
        style={
            'border': '2px solid black',  # Black border
            'padding': '10px',           # Padding inside the box
            'margin-bottom': '20px',      # Space between the boxes
            'height': '1000px',
            # 'width': '100%'
        }
    ),
    dcc.Interval(
        id='interval-component',
        interval=10000,  # Update every second
        n_intervals=0
    )
])

@app.callback(
    Output('weatherMap', 'figure'),
    Input('interval-component', 'n_intervals')
)
def alwaysUpdatingComponents(n):
    df = get_data()
    fig = map_of_Ireland(df)

    return fig

