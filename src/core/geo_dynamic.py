import math
import pandas as pd
import geopandas as gpd
import numpy as np
import json
import locale
from os.path import dirname, join
from bokeh.io import show, curdoc
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, HoverTool, ColorBar, Select, CustomJS
from bokeh.layouts import column
from bokeh.palettes import brewer

PALETTE_SIZE = 8

# geomap
geoDataFrame = gpd.read_file(
    join(dirname(__file__), 'datasets', 'countries_110m', 'ne_110m_admin_0_countries.shp'))[['ADMIN', 'ADM0_A3', 'geometry']]
geoDataFrame.columns = ['country', 'country_code', 'geometry']
# drop Antarctica
# print(geoDataFrame[geoDataFrame['country'] == 'Antarctica'])
geoDataFrame = geoDataFrame.drop(geoDataFrame.index[159])
geoDataFrame.head()


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
print(datasetRaw)

covidDataFrame = datasetRaw.groupby(['iso_code'], as_index=False).sum()


# format numbers to en_US locale for better readability
locale.setlocale(locale.LC_ALL, 'en_US')
covidDataFrame['new_cases_formatted'] = [locale.format_string(
    "%d", value, grouping=True) for value in covidDataFrame['new_cases'].values]
covidDataFrame['new_deaths_formatted'] = [locale.format_string(
    "%d", value, grouping=True) for value in covidDataFrame['new_deaths'].values]


# print(covidDataFrame[covidDataFrame['iso_code'] == 'USA'])
# print(covidDataFrame[covidDataFrame['iso_code'] == 'IND'])
# covidDataFrame.head()


def normalizedTotalCases():
    # new_cases is used here as it will contain the cumulative data as we sum() during grouping
    maxValue = max(covidDataFrame['new_cases'].values)
    minValue = min(covidDataFrame['new_cases'].values)
    delta = maxValue - minValue
    c = PALETTE_SIZE / math.log2(maxValue)
    covidDataFrame['normalized_total_cases'] = [
        c * math.log2(1 + value) for value in covidDataFrame['new_cases'].values]


def normalizedTotalDeaths():
    # new_deaths is used here as it will contain the cumulative data as we sum() during grouping
    maxValue = max(covidDataFrame['new_deaths'].values)
    minValue = min(covidDataFrame['new_deaths'].values)
    delta = maxValue - minValue
    c = PALETTE_SIZE / math.log2(maxValue)
    covidDataFrame['normalized_total_deaths'] = [
        c * math.log2(1 + value) for value in covidDataFrame['new_deaths'].values]


normalizedTotalCases()
normalizedTotalDeaths()

geoDataFrame = geoDataFrame.merge(
    covidDataFrame, left_on='country_code', right_on='iso_code', how='left')
jsonGeoData = json.loads(geoDataFrame.to_json())
source = GeoJSONDataSource(geojson=json.dumps(jsonGeoData))

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

plot = figure(plot_height=600, plot_width=1000, toolbar_location=None)


def init():
    plot.add_layout(color_bar, 'below')
    plot.axis.visible = False
    # plot.xgrid.grid_line_color = None
    # plot.ygrid.grid_line_color = None
    patch = plot.patches(xs="xs", ys="ys", source=source,
                         fill_color={'field': 'normalized_total_cases', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")

    plot.add_tools(HoverTool(tooltips=[('Country', '@country'), ('Total Cases',
                                                                 '@new_cases_formatted'), ('Total Deaths', '@new_deaths_formatted')], renderers=[patch]))
    plot.title.text = 'Total Cases Plot'


def generatePatchBasedOnSelect(selectValue):
    if selectValue == 'Total Cases':
        return plot.patches(xs="xs", ys="ys", source=source,
                            fill_color={'field': 'normalized_total_cases', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")
    elif selectValue == 'Total Deaths':
        return plot.patches(xs="xs", ys="ys", source=source,
                            fill_color={'field': 'normalized_total_deaths', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")


def handleSelectorChange(attrname, old, new):
    print(attrname, old, new)
    patch = generatePatchBasedOnSelect(selector.value)
    plot.add_tools(HoverTool(tooltips=[('Country', '@country'), ('Total Cases',
                                                                 '@new_cases_formatted'), ('Total Deaths', '@new_deaths_formatted')], renderers=[patch]))
    plot.title.text = '%s Plot' % (selector.value)


selectOptions = ['Total Cases', 'Total Deaths']
selector = Select(value=selectOptions[0], options=selectOptions)
selector.on_change('value', handleSelectorChange)

# initialize the plot
init()

layout = column(selector, plot)
curdoc().add_root(layout)
