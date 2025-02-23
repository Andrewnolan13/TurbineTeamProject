from plotly import express as px
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
            .update_layout(yaxis2 = dict(side = 'right'))
            .update_traces(selector = dict(name = 'EnvirTemp'), yaxis = 'y2', line = dict(width = 1,color = 'green'))
            .update_traces(selector = dict(name = 'WindSpeed'), yaxis = 'y2', line = dict(width = 1,color = 'blue'))
            .update_traces(selector = dict(name = 'WindDirAbs'), line = dict(width = 1,color = 'orange'))
            .update_traces(selector = dict(name = 'PowerPrediction'), line = dict(width = 4,color = 'red'))
            .update_layout(title_x = 0.5)
            .update_layout(uirevision='None')
        )