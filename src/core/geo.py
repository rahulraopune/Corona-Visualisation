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
from bokeh.models import GeoJSONDataSource, LinearColorMapper, HoverTool, ColorBar, Select
from bokeh.layouts import row, column
from bokeh.palettes import brewer
from bokeh.events import Tap
from geopy.geocoders import Nominatim

PALETTE_SIZE = 8

# geomap
geoDataFrame = gpd.read_file(
    join(dirname(__file__), 'datasets', 'countries_110m', 'ne_110m_admin_0_countries.shp'))[['ADMIN', 'ADM0_A3', 'geometry']]
geoDataFrame.columns = ['country', 'country_code', 'geometry']
# drop Antarctica
# print(geoDataFrame[geoDataFrame['country'] == 'Antarctica'])
geoDataFrame = geoDataFrame.drop(geoDataFrame.index[159])
geoDataFrame.head()
selectedCountryIsoCode = 'IND'


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


# format numbers to en_US locale for better readability
locale.setlocale(locale.LC_ALL, 'en_US')
covidDataFrame['total_cases_formatted'] = [locale.format_string(
    "%d", value, grouping=True) for value in covidDataFrame['total_cases']]
covidDataFrame['total_deaths_formatted'] = [locale.format_string(
    "%d", value, grouping=True) for value in covidDataFrame['total_deaths']]


# print(covidDataFrame[covidDataFrame['iso_code'] == 'USA'])
# print(covidDataFrame[covidDataFrame['iso_code'] == 'IND'])
# covidDataFrame.head()


def normalizedTotalCases():
    maxValue = max(covidDataFrame['total_cases'].values)
    minValue = min(covidDataFrame['total_cases'].values)
    delta = maxValue - minValue
    c = PALETTE_SIZE / math.log2(maxValue)
    covidDataFrame['normalized_total_cases'] = [
        c * math.log2(1 + value) for value in covidDataFrame['total_cases']]


def normalizedTotalDeaths():
    maxValue = max(covidDataFrame['total_deaths'].values)
    minValue = min(covidDataFrame['total_deaths'].values)
    delta = maxValue - minValue
    c = PALETTE_SIZE / math.log2(maxValue)
    covidDataFrame['normalized_total_deaths'] = [
        c * math.log2(1 + value) for value in covidDataFrame['total_deaths']]


def normalizedTotalCasesPerMillion():
    maxValue = max(covidDataFrame['total_cases_per_million'].values)
    minValue = min(covidDataFrame['total_cases_per_million'].values)
    delta = maxValue - minValue
    c = PALETTE_SIZE / math.log2(maxValue)
    covidDataFrame['normalized_total_cases_per_million'] = [
        c * math.log2(1 + value) for value in covidDataFrame['total_cases_per_million']]


def normalizedTotalDeathsPerMillion():
    maxValue = max(covidDataFrame['total_cases_per_million'].values)
    minValue = min(covidDataFrame['total_cases_per_million'].values)
    delta = maxValue - minValue
    c = PALETTE_SIZE / math.log2(maxValue)
    covidDataFrame['normalized_total_deaths_per_million'] = [
        c * math.log2(1 + value) for value in covidDataFrame['total_deaths_per_million']]


normalizedTotalCases()
normalizedTotalDeaths()
normalizedTotalCasesPerMillion()
normalizedTotalDeathsPerMillion()

geoDataFrame = geoDataFrame.merge(
    covidDataFrame, left_on='country_code', right_on='iso_code', how='left')
# convert date column to string as datetime dtype cannot be converted as JSON
geoDataFrame['date'] = geoDataFrame['date'].astype(str)
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

geoPlot = figure(plot_height=600, plot_width=1000,
                 tools="pan,wheel_zoom,reset,hover,save")
linePlot = figure(plot_height=600, plot_width=600)
barPlot = figure(plot_height=600, plot_width=1200)


def init():
    geoPlot.add_layout(color_bar, 'below')
    geoPlot.axis.visible = False
    # geoPlot.xgrid.grid_line_color = None
    # geoPlot.ygrid.grid_line_color = None
    patch = geoPlot.patches(xs="xs", ys="ys", source=source,
                            fill_color={'field': 'normalized_total_cases', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")

    geoPlot.add_tools(HoverTool(tooltips=[('Country', '@country'), ('Total Cases',
                                                                    '@total_cases_formatted'), ('Total Deaths', '@total_deaths_formatted')], renderers=[patch]))
    geoPlot.title.text = 'Total Cases Plot'


def generatePatchBasedOnSelect(selectValue):
    if selectValue == 'Total Cases':
        return geoPlot.patches(xs="xs", ys="ys", source=source,
                               fill_color={'field': 'normalized_total_cases', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")
    elif selectValue == 'Total Deaths':
        return geoPlot.patches(xs="xs", ys="ys", source=source,
                               fill_color={'field': 'normalized_total_deaths', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")
    elif selectValue == 'Total Cases Per Million':
        return geoPlot.patches(xs="xs", ys="ys", source=source,
                               fill_color={'field': 'normalized_total_cases_per_million', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")
    elif selectValue == 'Total Deaths Per Million':
        return geoPlot.patches(xs="xs", ys="ys", source=source,
                               fill_color={'field': 'normalized_total_deaths_per_million', 'transform': color_mapper}, line_color='black', line_width=0.35, fill_alpha=1, hover_fill_color="#fec44f")


def findCountry(coord):
    country = Nominatim(user_agent="geoapiExercises",
                        ssl_context=ssl.SSLContext()).reverse(coord, exactly_one=True).raw['address'].get('country', '')
    print(country)
    if country == 'Россия':
        return 'Russia'
    elif country == 'China 中国':
        return 'China'
    elif country == 'الجزائر':
        return 'Algeria'
    elif country == 'Deutschland':
        return 'Germany'
    elif country == 'Libya / ليبيا':
        return 'Libya'
    elif country == 'Česká republika':
        return 'Slovakia'
    return country


def handleSelectorChange(attrname, old, new):
    print(attrname, old, new)
    patch = generatePatchBasedOnSelect(selector.value)
    geoPlot.add_tools(HoverTool(tooltips=[('Country', '@country'), ('Total Cases',
                                                                    '@total_cases_formatted'), ('Total Deaths', '@total_deaths_formatted')], renderers=[patch]))
    geoPlot.title.text = '%s Plot' % (selector.value)


def handleTap(model):
    country = findCountry((model.y, model.x))
    selectedCountryIsoCode = geoDataFrame[geoDataFrame['country']
                                          == country]['iso_code'].values[0]

    # TODO: change line plot and bar plot here                                          
    print(selectedCountryIsoCode)
    return selectedCountryIsoCode


selectOptions = ['Total Cases', 'Total Deaths',
                 'Total Cases Per Million', 'Total Deaths Per Million']
selector = Select(value=selectOptions[0], options=selectOptions)
selector.on_change('value', handleSelectorChange)
geoPlot.on_event(Tap, handleTap)

# initialize the geoPlot
init()

layout = column(row(column(selector, geoPlot), linePlot), row(barPlot))
curdoc().add_root(layout)


############################################################################
# Sachin Code impplementation

import pandas as pandaRef

#Copy of the dataFrame
dataFrameRef=datasetRaw


def cleanDataFrame_Country(dataFrameRef, countryCode):
    
    # drop World data and drop iso_code with NaN values
    dataFrameRef = dataFrameRef[dataFrameRef.iso_code != 'OWID_WRL']

    # Add new Year/Month Col and formatted the Year-Month-Day date field to Year/Month
    dataFrameRef['Year/Month'] = pandaRef.to_datetime(dataFrameRef['date']).apply(lambda x: '{year}/{month}'.format(year=x.year, month=x.month))
    # sort by date in descending
    dataFrameRef = dataFrameRef.sort_values(by='date', ascending=True)

    # select unique country values (as data is sorted in descending based on date and head 1 will give the most recent record of a country)
    uniqueDataFrame = dataFrameRef.groupby(['iso_code'], as_index=False).tail(1)

    #print(uniqueDataFrame)

    # sort by date in descending
    #uniqueDataFrame = uniqueDataFrame.sort_values(by='total_cases', ascending=False)
    #uniqueDataFrame = uniqueDataFrame.head(20)

    #top20country = uniqueDataFrame['location']

    
    countryDataFrame = dataFrameRef[dataFrameRef.iso_code == countryCode]
    print(countryDataFrame)
    return countryDataFrame


countryDataFrame = cleanDataFrame_Country(dataFrameRef, selectedCountryIsoCode)


