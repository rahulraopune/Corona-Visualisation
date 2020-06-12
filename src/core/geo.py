import math
import pandas as pd
import geopandas as gpd
import numpy as np
import json
from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, HoverTool, ColorBar
from bokeh.palettes import brewer
import locale

# geomap
geoDataFrame = gpd.read_file(
    'datasets/countries_110m/ne_110m_admin_0_countries.shp')[['ADMIN', 'ADM0_A3', 'geometry']]
geoDataFrame.columns = ['country', 'country_code', 'geometry']
# drop Antarctica
# print(geoDataFrame[geoDataFrame['country'] == 'Antarctica'])
geoDataFrame = geoDataFrame.drop(geoDataFrame.index[159])
geoDataFrame.head()


# COVID-19 dataset
datasetRaw = pd.read_csv('datasets/owid-covid-data.csv')
covidDataFrame = datasetRaw.groupby(['iso_code'], as_index=False).sum()
# drop World data
# print(covidDataFrame[covidDataFrame['iso_code'] == 'OWID_WRL']['new_cases'])
covidDataFrame = covidDataFrame.drop(covidDataFrame.index[150])
# normalize values
maxValue = max(covidDataFrame['new_cases'].values)
minValue = min(covidDataFrame['new_cases'].values)
delta = maxValue - minValue
c = 8 / math.log2(maxValue)
covidDataFrame['normalized_new_cases'] = [
    c * math.log2(1 + value) for value in covidDataFrame['new_cases'].values]

# format numbers to US locale for better readability
locale.setlocale(locale.LC_ALL, 'en_US')
covidDataFrame['new_cases_formatted'] = [locale.format_string(
    "%d", value, grouping=True) for value in covidDataFrame['new_cases'].values]
covidDataFrame['new_deaths_formatted'] = [locale.format_string(
    "%d", value, grouping=True) for value in covidDataFrame['new_deaths'].values]

# print(covidDataFrame[covidDataFrame['iso_code'] == 'USA'])
# print(covidDataFrame[covidDataFrame['iso_code'] == 'IND'])
covidDataFrame.head()


geoDataFrame = geoDataFrame.merge(
    covidDataFrame, left_on='country_code', right_on='iso_code', how='left')


# sequential multi-hue color palette.
palette = brewer['YlGnBu'][8]
# reverse color order so that dark blue is highest obesity.
palette = palette[::-1]
color_mapper = LinearColorMapper(palette=palette, low=0, high=8)
# define custom tick labels for color bar.
# tick_labels = {'0': '0%', '5': '5%', '10': '10%', '15': '15%',
#                '20': '20%', '25': '25%', '30': '30%', '35': '35%', '40': '>40%'}
# Create color bar.
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8, width=500, height=20,
                     border_line_color=None, location=(0, 0), orientation='horizontal')


plot = figure(title='Worldwide Spread of COVID-19',
              plot_height=800, plot_width=1500, toolbar_location=None)
plot.add_layout(color_bar, 'below')
plot.axis.visible = False
# plot.xgrid.grid_line_color = None
# plot.ygrid.grid_line_color = None

jsonGeoData = json.loads(geoDataFrame.to_json())
patch = plot.patches(xs="xs", ys="ys", source=GeoJSONDataSource(geojson=json.dumps(jsonGeoData)),
                     fill_color={'field': 'normalized_new_cases', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")


plot.add_tools(HoverTool(tooltips=[('Country', '@country'), ('Total Cases',
                                                             '@new_cases_formatted'), ('Total Deaths', '@new_deaths_formatted')], renderers=[patch]))

show(plot)
