from bokeh.transform import factor_cmap
import pandas as pandaRef
import math
import pandas as pd
import random
import geopandas as gpd
import numpy as np
import json
import locale
import ssl
from os.path import dirname, join
from bokeh.io import show, curdoc
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, HoverTool, ColorBar, Select, ColumnDataSource, DatetimeTickFormatter
from bokeh.layouts import row, column
from bokeh.palettes import brewer, Spectral5, Category20c
from bokeh.events import Tap
from geopy.geocoders import Nominatim
from bokeh.transform import cumsum

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
selectedCountryName = 'India'


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

geoPlot = figure(plot_height=600, plot_width=1000)

# TODO: modify according to line --> RAHUL
linePlot = figure(plot_height=600, plot_width=600,
                  x_axis_type="datetime", title="Country")

months = ['2019/12', '2020/1', '2020/2',
          '2020/3', '2020/4', '2020/5', '2020/6']
barPlot = figure(plot_height=600, plot_width=1200, x_range=months, title="Time Series Plot",
                 toolbar_location=None)
piePlot = figure(plot_height=600, plot_width=600,
                 title="Pie Chart", x_range=(-0.5, 1.0))


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
    return Nominatim(user_agent="geoapiExercises",
                     ssl_context=ssl.SSLContext()).reverse(coord, exactly_one=True, language='en').raw['address'].get('country', '')


def getSelectorParam():
    if selector.value == 'Total Cases':
        return 'total_cases'
    elif selector.value == 'Total Deaths':
        return 'total_deaths'
    elif selector.value == 'Total Cases Per Million':
        return 'total_cases_per_million'
    elif selector.value == 'Total Deaths Per Million':
        return 'total_deaths_per_million'


def handleSelectorChange(attrname, old, new):
    print(attrname, old, new)
    patch = generatePatchBasedOnSelect(selector.value)
    geoPlot.add_tools(HoverTool(tooltips=[('Country', '@country'), ('Total Cases',
                                                                    '@total_cases_formatted'), ('Total Deaths', '@total_deaths_formatted')], renderers=[patch]))
    geoPlot.title.text = '%s Plot' % (selector.value)

    linePlotCountryTotalCases(selectedCountryIsoCode,
                              selectedCountryName, param=getSelectorParam())


################################
############################################################################
############################################################################
# Sachin Code impplementation


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

    # print(uniqueDataFrame)

    # sort by date in descending
    #uniqueDataFrame = uniqueDataFrame.sort_values(by='total_cases', ascending=False)
    #uniqueDataFrame = uniqueDataFrame.head(20)

    #top20country = uniqueDataFrame['location']

    countryDataFrame = dataFrameRef[dataFrameRef.iso_code == countryCode]
    return countryDataFrame


def linePlotCountryTotalCases(selectedCountryIsoCode, country, param='total_cases'):
    # clear line plot from current document
    row1 = curdoc().get_model_by_name('row1')
    row1Child = row1.children
    linePlotLayout = curdoc().get_model_by_name('line_plot')
    row1Child.remove(linePlotLayout)

    linePlot = figure(plot_height=600, plot_width=600,
                      x_axis_type="datetime", title="Country")
    countryDataFrame = cleanDataFrameCountry(selectedCountryIsoCode)
    data = pd.pivot_table(countryDataFrame, index='date',
                          columns='iso_code', values=param).reset_index()
    linePlot.grid.grid_line_alpha = 0.1
    linePlot.xaxis.axis_label = 'Date'
    linePlot.yaxis.axis_label = param
    linePlot.title.text = 'Timeseries %s Plot of %s' % (
        selector.value, country)
    linePlot.yaxis.formatter.use_scientific = False
    linePlot.xaxis.formatter = DatetimeTickFormatter(
        hours=["%d %B %Y"], days=["%d %B %Y"], months=["%d %B %Y"], years=["%d %B %Y"])
    # linePlot.legend = False
    linePlot.line(np.array(data['date'], dtype=np.datetime64),
                  data[selectedCountryIsoCode], color="cyan", legend_label=country, line_width=3)
    # add new line plot to current document
    row1Child.append(row(linePlot, name='line_plot'))


def barPlotCountryTotalCases(isoCode, countryName):
    countryDataFrame = cleanDataFrameCountry(isoCode)
    group = countryDataFrame.groupby('YearMonth', as_index=False).sum()
    barPlot.vbar(x=months, top=group['total_cases'].values, width=0.9)
    barPlot.title.text = 'Total Cases - %s' % (countryName)
    barPlot.xgrid.grid_line_color = None
    barPlot.y_range.start = 0


def piePlotForCountry(isoCode, countryName):
    countryDataFrame = cleanDataFrameCountry(isoCode).tail(1)
    # selectionJson = countryDataFrame[[
    #     'population', 'total_cases', 'total_deaths']].to_json(orient='records')
    #     # .iloc[0].values
    #     #
    # selectionJson = json.dumps(selectionJson)
    # data = pd.Series(selectionJson).reset_index(
    #     name='value').rename(columns={'index': 'country'})

    # print(data['value'].values)
    # data['angle'] = data['value']/data['value'].sum() * 2*pi
    # data['color'] = Category20c[len(selectionJson)]
    # piePlot.wedge(x=0, y=1, radius=0.4,
    #               start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
    #               line_color="white", fill_color='color', legend='country', source=data)
    piePlot.title.text = 'COVID-19 Distribution - %s' % (countryName)


def handleTap(model):
    global selectedCountryName
    global selectedCountryIsoCode

    selectedCountryName = findCountry((model.y, model.x))
    selectedCountryIsoCode = geoDataFrame[geoDataFrame['country']
                                          == selectedCountryName]['iso_code'].values[0]
    # TODO: change line plot and bar plot here
    barPlotCountryTotalCases(selectedCountryIsoCode,
                             selectedCountryName)
    piePlotForCountry(selectedCountryIsoCode, selectedCountryName)
    linePlotCountryTotalCases(selectedCountryIsoCode,
                              selectedCountryName, getSelectorParam())
    # print(selectedCountryIsoCode)


selectOptions = ['Total Cases', 'Total Deaths',
                 'Total Cases Per Million', 'Total Deaths Per Million']
selector = Select(value=selectOptions[0], options=selectOptions)
selector.on_change('value', handleSelectorChange)
geoPlot.on_event(Tap, handleTap)

# initialize the geoPlot
init()

layout = column(row(column(selector, geoPlot), row(linePlot, name='line_plot'),
                    name='row1'), row(barPlot, piePlot, name='row2'), name='mainLayout')
curdoc().add_root(layout)
