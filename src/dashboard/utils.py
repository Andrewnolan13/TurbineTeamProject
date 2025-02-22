from plotly import express as px
import pandas as pd

def map_of_Ireland(df:pd.DataFrame)->px.scatter_mapbox:
    fig = px.scatter_mapbox(df, lat='latitude', lon='longitude',
                            color='temperature', size_max=10,
                            color_continuous_scale='plasma',
                            zoom=6, mapbox_style='open-street-map')
    # fig.update_layout(width = 800, height = 800)
    return fig.update_layout(uirevision='None')