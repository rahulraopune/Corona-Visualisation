import math
import pandas as pd
import geopandas as gpd
import numpy as np
import json
from bokeh.io import show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, HoverTool, ColorBar
from bokeh.palettes import brewer

# geomap
geoDataFrame = gpd.read_file(
    'datasets/countries_110m/ne_110m_admin_0_countries.shp')[['ADMIN', 'ADM0_A3', 'geometry']]
geoDataFrame.columns = ['country', 'country_code', 'geometry']
# drop Antarctica
# print(geoDataFrame[geoDataFrame['country'] == 'Antarctica'])
geoDataFrame = geoDataFrame.drop(geoDataFrame.index[159])
geoDataFrame.head()


# COVID-19 dataset
covidDataFrame = pd.read_csv(
    'datasets/owid-covid-data.csv').groupby(['iso_code'], as_index=False).sum()
# drop World data
print(covidDataFrame[covidDataFrame['iso_code'] == 'OWID_WRL']['new_cases'])
covidDataFrame = covidDataFrame.drop(covidDataFrame.index[150])
# normalize values
maxValue = max(covidDataFrame['new_cases'].values)
minValue = min(covidDataFrame['new_cases'].values)
delta = maxValue - minValue
c = 8 / math.log2(maxValue)
covidDataFrame['normalized_new_cases'] = [ c * math.log2(1 + value) for value in covidDataFrame['new_cases'].values]

# print(covidDataFrame[covidDataFrame['iso_code'] == 'USA'])
# print(covidDataFrame[covidDataFrame['iso_code'] == 'IND'])
covidDataFrame.head()


geoDataFrame = geoDataFrame.merge(
    covidDataFrame, left_on='country_code', right_on='iso_code')


# Define a sequential multi-hue color palette.
palette = brewer['YlGnBu'][8]
# Reverse color order so that dark blue is highest obesity.
palette = palette[::-1]
# Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
color_mapper = LinearColorMapper(palette=palette, low=0, high=8)
# Define custom tick labels for color bar.
# tick_labels = {'0': '0%', '5': '5%', '10': '10%', '15': '15%',
#                '20': '20%', '25': '25%', '30': '30%', '35': '35%', '40': '>40%'}
# Create color bar.
color_bar = ColorBar(color_mapper=color_mapper, label_standoff=8, width=500, height=20,
                     border_line_color=None, location=(0, 0), orientation='horizontal')


plot = figure(title='Worldwide Spread of COVID-19',
              plot_height=800, plot_width=1500, toolbar_location=None)
plot.xgrid.grid_line_color = None
plot.ygrid.grid_line_color = None

# Specify figure layout.
plot.add_layout(color_bar, 'below')

jsonGeoData = json.loads(geoDataFrame.to_json())
patch = plot.patches(xs="xs", ys="ys", source=GeoJSONDataSource(geojson=json.dumps(jsonGeoData)),
                     fill_color={'field': 'normalized_new_cases', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")


# point = plot.circle('longitude', 'latitude', source=ColumnDataSource(geoCovid),
#                     radius='scaled_total_cases', alpha=0.2)

plot.add_tools(HoverTool(tooltips=[('Country', '@country'), ('Total Cases',
                                                             '@new_cases'), ('Total Deaths', '@new_deaths')], renderers=[patch]))

show(plot)

# print(geoCovid)
# print(geoCovid[geoCovid['location'] == 'India'])
