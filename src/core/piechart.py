from math import pi

import pandas as pd
from bokeh.transform import factor_cmap
import pandas as pandaRef
import math
import pandas as pd
import geopandas as gpd
import numpy as np
import json
import locale
import ssl
from os.path import dirname, join
from bokeh.io import show, curdoc
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, HoverTool, ColorBar, Select, ColumnDataSource
from bokeh.layouts import row, column
from bokeh.palettes import brewer, Spectral5, Category20c,mpl
from bokeh.events import Tap
from geopy.geocoders import Nominatim
from bokeh.transform import cumsum
from math import pi

from bokeh.io import output_file, show
from bokeh.palettes import Category20c
from bokeh.plotting import figure
from bokeh.transform import cumsum

output_file("pie.html")

# COVID-19 dataset
datasetRaw = pd.read_csv(
    join(dirname(__file__), 'datasets', 'owid-covid-data.csv'))
# drop World data and drop iso_code with NaN values
datasetRaw = datasetRaw[datasetRaw.iso_code != 'OWID_WRL']
datasetRaw = datasetRaw.dropna(subset=['iso_code'])
# convert date column to pandas date
datasetRaw['date'] = pd.to_datetime(datasetRaw.date)
# sort by date in descending
datasetRaw = datasetRaw.sort_values(by='date', ascending=False)
# print(datasetRaw)
# select unique country values (as data is sorted in descending based on date and head 1 will give the most recent record of a country)
covidDataFrame = datasetRaw.groupby(['iso_code'], as_index=False).head(1)

def cleanDataFrameCountry(countryCode):
    dataFrameRef = datasetRaw
    # Add new Year/Month Col and formatted the Year-Month-Day date field to Year/Month
    dataFrameRef['YearMonth'] = pandaRef.to_datetime(dataFrameRef['date']).apply(
        lambda x: '{year}/{month}'.format(year=x.year, month=x.month))
    # sort by date in descending
    dataFrameRef = dataFrameRef.sort_values(by='date', ascending=True)

    # select unique country values (as data is sorted in descending based on date and head 1 will give the most recent record of a country)
    uniqueDataFrame = dataFrameRef.groupby(
        ['iso_code'], as_index=False).tail(1)
    countryDataFrame = dataFrameRef[dataFrameRef.iso_code == countryCode]
    return countryDataFrame

def piePlot(covidDataFrame,isoCode):
    df = covidDataFrame
    raw_data = df[['iso_code', 'continent', 'total_cases', 'total_deaths', 'new_cases', 'new_deaths']].to_json(
        orient='records')
    json_data = json.loads(raw_data)
    for dict_item in json_data:
        for key in dict_item:
            if dict_item[key] == isoCode:
                selected_keys = ['total_cases', 'total_deaths', 'new_cases', 'new_deaths']
                new_dict = {k: dict_item[k] for k in selected_keys}

    pc_data = pd.Series(new_dict).reset_index(name='value').rename(columns={'index': 'stats'})
    pc_data['angle'] = pc_data['value'] / pc_data['value'].sum() * 2 * pi
    pc_data['color'] = mpl['Plasma'][len(new_dict)]

    p = figure(plot_height=350, title="Pie Chart", toolbar_location=None,
               tools="hover", tooltips="@stats:@value", x_range=(-0.5, 1.0))

    p.wedge(x=0, y=1, radius=0.4,
            start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
            line_color="white", fill_color='color', legend_field='stats', source=pc_data)

    p.axis.axis_label = None
    p.axis.visible = False
    p.grid.grid_line_color = None

    show(p)


def main():
    dataFrame =covidDataFrame
    isoCode = "IND"
    piePlot(dataFrame, isoCode)

if __name__ == "__main__":
    main()