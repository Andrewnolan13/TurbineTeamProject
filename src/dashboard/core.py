import dash
from dash import dcc, html
from dash.dependencies import Input, Output

import pandas as pd
import sqlite3

from .utils import map_of_Ireland, plot_real_time_predictions
from ..constants import SOURCE

# Placeholder function for getting data
def get_data():
    conn = sqlite3.connect(SOURCE.DATA.DB.str)
    df = pd.read_sql_query("SELECT * FROM real_time_predictions", conn)
    return df

initialDataFrame = get_data()

app = dash.Dash(__name__)
app.layout = html.Div([
    html.Div(id = 'title',children='Real-time Wind Turbine Forecasting Dashboard',style={'textAlign':'center','fontSize':40}),
    html.Div(
        dcc.Graph(id='predictionMap', figure=plot_real_time_predictions(initialDataFrame.copy()),config={'displayModeBar': False},style={'height':'100%', 'width':'100%'}), 
        style={
            'border': '2px solid black',  # Black border
            'padding': '10px',           # Padding inside the box
            'margin-bottom': '20px',      # Space between the boxes
            'height': '1000px',
        }
    ),
    dcc.Interval(
        id='interval-component',
        interval=1000,  # Update every second
        n_intervals=0
    )
])

@app.callback(
    Output('predictionMap', 'figure'),
    Input('interval-component', 'n_intervals')
)
def alwaysUpdatingComponents(n):
    print(f"Updating component {n}")
    df = get_data()
    fig = plot_real_time_predictions(df)

    return fig

