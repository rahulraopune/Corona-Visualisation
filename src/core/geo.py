from collections import OrderedDict
import datetime
from bokeh.transform import factor_cmap, dodge
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
from bokeh.palettes import brewer, Spectral5, Category20c, Category10
from bokeh.events import Tap
from geopy.geocoders import Nominatim
from bokeh.transform import cumsum
from math import pi

from datetime import datetime

from pandas.core.frame import DataFrame

PALETTE_SIZE = 8

# geomap
geoDataFrame = gpd.read_file(
    join(dirname(__file__), 'datasets', 'countries_110m', 'ne_110m_admin_0_countries.shp'))[['ADMIN', 'ADM0_A3', 'geometry']]
geoDataFrame.columns = ['country', 'country_code', 'geometry']
# drop Antarctica
# print(geoDataFrame[geoDataFrame['country'] == 'Antarctica'])
geoDataFrame = geoDataFrame.drop(geoDataFrame.index[159])
geoDataFrame.head()

selectedCountryIsoCode = 'DEU'
selectedCountryName = 'Germany'


# COVID-19 dataset
datasetRaw = pd.read_csv(
    join(dirname(__file__), 'datasets', 'owid-covid-data.csv'))
# drop World data and drop iso_code with NaN values
datasetRaw = datasetRaw[datasetRaw.iso_code != 'OWID_WRL']
datasetRaw = datasetRaw.dropna(subset=['iso_code', 'total_cases'])
# convert date column to pandas date
datasetRaw['date'] = pd.to_datetime(datasetRaw.date)
# sort by date in descending
datasetRaw = datasetRaw.sort_values(by='date', ascending=False)
# print(datasetRaw)
# select unique country values (as data is sorted in descending based on date and head 1 will give the most recent record of a country)
covidDataFrame = datasetRaw.groupby(['iso_code'], as_index=False).head(1)


# cases dataset
casesDatasetRaw = pd.read_csv(
    join(dirname(__file__), 'datasets', 'datasets_494766_1283557_country_wise_latest.csv'))
casesDataset = covidDataFrame.merge(
    casesDatasetRaw, how='left', left_on='location', right_on='Country/Region')
# print(casesDataset[casesDataset['iso_code'] == 'IND']['Active'])
sortedCasesDataset = casesDataset.sort_values(by='date', ascending=True)
dodgeInput = DataFrame(sortedCasesDataset, columns=['iso_code',
                                                    'Deaths', 'Recovered', 'Active', 'WHO Region', 'Country/Region'])

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

geoPlot = figure(plot_height=600, plot_width=1000, toolbar_location=None)

# line init
linePlot = figure(plot_height=600, plot_width=600,
                  x_axis_type="datetime", title="Country", toolbar_location=None)

########## Bar Plot Start-Init #######################

covidDataFrame1 = datasetRaw
covidDataFrame1 = covidDataFrame1.sort_values(by='date', ascending=True)
covidDataFrame1['weekno'] = covidDataFrame1['date'].dt.strftime('%U')

weekno = covidDataFrame1['weekno'].values
uniweekno = list(OrderedDict.fromkeys(weekno))
uniweeknostr = [x for x in uniweekno]

# bar plot init
barPlot = figure(plot_height=600, plot_width=1000, x_range=uniweeknostr, title="Time Series Plot",
                 toolbar_location=None)
########## Bar Plot END-Init #######################

piePlot = figure(plot_height=600, plot_width=450, tools="hover", tooltips="@stats:@value",
                 title="Pie Chart", x_range=(-0.5, 1.0))

continentBarPlot = figure(plot_height=600, plot_width=1400, x_range=[], title="Time Series Plot",
                          toolbar_location=None)


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

    barPlotCountryTotalCases(selectedCountryIsoCode,
                             selectedCountryName, getSelectorParam(), isInit=True)
    piePlotForCountry(selectedCountryIsoCode, selectedCountryName, isInit=True)
    linePlotCountryTotalCases(selectedCountryIsoCode,
                              selectedCountryName, getSelectorParam(), isInit=True)
    barPlotForContinent(selectedCountryIsoCode,
                        selectedCountryName, isInit=True)

    layout = column(row(column(selector, geoPlot),
                        row(linePlot, name='line_plot'),
                        name='row1'), row(column(barPlot, name='bar_column'), column(piePlot, name='pie_column'), name='row2'), row(continentBarPlot, name='row3'), name='mainLayout')
    curdoc().add_root(layout)


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
    # print(attrname, old, new)
    patch = generatePatchBasedOnSelect(selector.value)
    geoPlot.add_tools(HoverTool(tooltips=[('Country', '@country'), ('Total Cases',
                                                                    '@total_cases_formatted'), ('Total Deaths', '@total_deaths_formatted')], renderers=[patch]))
    geoPlot.title.text = '%s Plot' % (selector.value)

    linePlotCountryTotalCases(selectedCountryIsoCode,
                              selectedCountryName, param=getSelectorParam())

    barPlotCountryTotalCases(selectedCountryIsoCode,
                             selectedCountryName, param=getSelectorParam())

    barPlotForContinent(selectedCountryIsoCode,
                        selectedCountryName)

################################
# clean the dataframe for the country selected during interaction operation
# Addtion WeekNo, YearMonth columns added as required by subplots


def cleanDataFrameCountry(countryCode):
    dataFrameRef = datasetRaw
    # Add new Year/Month Col and formatted the Year-Month-Day date field to Year/Month
    dataFrameRef['YearMonth'] = pandaRef.to_datetime(dataFrameRef['date']).apply(
        lambda x: '{year}/{month}'.format(year=x.year, month=x.month))
    dataFrameRef['Month'] = pandaRef.to_datetime(dataFrameRef['date']).apply(
        lambda x: '{month}'.format(month=x.month))
    dataFrameRef['YearMonthDay'] = pandaRef.to_datetime(dataFrameRef['date']).apply(
        lambda x: '{year}/{month}/{day}'.format(year=x.year, month=x.month, day=x.day))

    dataFrameRef['WeekNo'] = dataFrameRef['date'].dt.strftime('%U')

    # sort by date in descending
    dataFrameRef = dataFrameRef.sort_values(by='date', ascending=True)

    countryDataFrame = dataFrameRef[dataFrameRef.iso_code == countryCode]

    return countryDataFrame


def linePlotCountryTotalCases(selectedCountryIsoCode, country, param='total_cases', isInit=False):
    global linePlot
    linePlot = figure(plot_height=600, plot_width=600,
                      x_axis_type="datetime", title="Country")
    countryDataFrame = cleanDataFrameCountry(selectedCountryIsoCode)
    data = pd.pivot_table(countryDataFrame, index='date',
                          columns='iso_code', values=param).reset_index()
    linePlot.grid.grid_line_alpha = 0.1
    linePlot.xaxis.axis_label = 'Date'
    linePlot.yaxis.axis_label = selector.value
    linePlot.title.text = 'Timeseries %s Plot of %s' % (
        selector.value, country)
    linePlot.yaxis.formatter.use_scientific = False
    linePlot.xaxis.formatter = DatetimeTickFormatter(
        hours=["%d %B %Y"], days=["%d %B %Y"], months=["%d %B %Y"], years=["%d %B %Y"])
    formattedDate = [pd.to_datetime(np.datetime_as_string(value, unit='D')).strftime(
        "%d %B %Y") for value in data['date'].values]

    formattedData = [locale.format_string(
        "%d", value, grouping=True) for value in data[selectedCountryIsoCode].values]
    source = ColumnDataSource(
        data={'x': np.array(data['date'], dtype=np.datetime64), 'y': data[selectedCountryIsoCode], 'data_str': formattedData, 'date_str': formattedDate})
    hover = HoverTool(
        tooltips=[('Date', '@date_str'), (selector.value, '@data_str')])
    linePlot.add_tools(hover)
    linePlot.line(x='x', y='y', source=source, color="orange",
                  legend_label=country, line_width=3)
    linePlot.legend.location = "top_left"
    linePlot.xaxis.major_label_orientation = 1

    if not isInit:
        # clear line plot from current document
        row1 = curdoc().get_model_by_name('row1')
        row1Child = row1.children
        linePlotLayout = curdoc().get_model_by_name('line_plot')
        row1Child.remove(linePlotLayout)
        # add new line plot to current document
        row1Child.append(row(linePlot, name='line_plot'))


def barPlotCountryTotalCases(selectedCountryIsoCode, country, param='total_cases', isInit=False):
    global barPlot
    global uniweeknostr
    # Recreate the SubPlot Layout
    barPlot = figure(plot_height=600, plot_width=1000, x_range=uniweeknostr, title="Time Series Plot",
                     toolbar_location=None)

    # Data Preprocessing
    countryDataFrame = cleanDataFrameCountry(selectedCountryIsoCode)

    # Group and Sum active cases into weekly
    group = countryDataFrame.groupby('WeekNo', as_index=False).sum()

    # Mapper from select param to active cases columns
    displayArg = ''
    if param == 'total_cases':  # for total_cases map to new_cases
        displayArg = 'new_cases'

    if param == 'total_deaths':  # for total_death map to new_deaths
        displayArg = 'new_deaths'

    if param == 'total_cases_per_million':  # for total_cases_per_million map to new_cases_per_million
        displayArg = 'new_cases_per_million'

    if param == 'total_deaths_per_million':  # for total_deaths_per_million map to new_deaths_per_million
        displayArg = 'new_deaths_per_million'

    # convert int weekno to str WeekNumber:00
    group['WeekNo'] = group['WeekNo'].astype(str)
    uniweeknostr = [x for x in uniweekno]

    # plot active cases for the param received
    barPlot.vbar(
        x=uniweeknostr, top=group[displayArg].values, width=0.9, color='indianred')

    # Mapper to format the str dispalyed in the browser
    if displayArg == 'new_cases':
        displayArg = 'New Cases'

    if displayArg == 'new_deaths':
        displayArg = 'New Deaths'

    if displayArg == 'new_cases_per_million':
        displayArg = 'New Cases Per Million'

    if displayArg == 'new_deaths_per_million':
        displayArg = 'New Deaths Per Million'

    barPlot.title.text = 'Weekly Reported %s - %s' % (displayArg, country)
    barPlot.xaxis.major_label_orientation = 1
    barPlot.yaxis.formatter.use_scientific = False
    barPlot.xaxis.axis_label = 'Week Number'
    barPlot.yaxis.axis_label = displayArg
    barPlot.xgrid.grid_line_color = None

    barPlot.y_range.start = 0

    if not isInit:
        # clear plots from current document
        mainLayout = curdoc().get_model_by_name('mainLayout')
        mainLayoutChild = mainLayout.children
        row2 = curdoc().get_model_by_name('row2')
        mainLayoutChild.remove(row2)
        # pie plot is added here just to maintain the layout order
        mainLayoutChild.append(row(column(barPlot, name='bar_column'),
                                   column(piePlot, name='pie_column'), name='row2'))


def piePlotForCountry(isoCode, selectedCountryName, isInit=False):
    sourceJson = (casesDataset[casesDataset['iso_code'] == isoCode][[
                  'Deaths', 'Recovered', 'Active']]).to_json(orient='records')
    json_data = json.loads(sourceJson)[0]

    pc_data = pd.Series(json_data).reset_index(
        name='value').rename(columns={'index': 'stats'})
    pc_data['percent'] = pc_data['value'] / pc_data['value'].sum() * 100
    pc_data['angle'] = pc_data['value']/pc_data['value'].sum() * 2 * pi
    pc_data['color'] = Category10[len(json_data)]

    global piePlot
    piePlot = figure(plot_height=600, plot_width=450,
                     title="Pie Chart", tools="hover", tooltips="@stats:@percent{0.2f} %", x_range=(-0.5, 1.0))
    piePlot.wedge(x=0, y=1, radius=0.4,
                  start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
                  line_color="white", fill_color='color', legend_field='stats', source=pc_data)
    piePlot.title.text = 'COVID-19 Distribution - %s' % (selectedCountryName)
    piePlot.axis.axis_label = None
    piePlot.axis.visible = False
    piePlot.grid.grid_line_color = None

    if not isInit:
        # clear plots from current document
        mainLayout = curdoc().get_model_by_name('mainLayout')
        mainLayoutChild = mainLayout.children
        row2 = curdoc().get_model_by_name('row2')
        mainLayoutChild.remove(row2)
        # bar plot is added here just to maintain the layout order
        mainLayoutChild.append(row(column(barPlot, name='bar_column'),
                                   column(piePlot, name='pie_column'), name='row2'))


def barPlotForContinent(selectedCountryIsoCode, selectedCountryName, isInit=False):
    global continentBarPlot
    selected_country = dodgeInput.loc[dodgeInput['iso_code']
                                      == selectedCountryIsoCode]
    selected_region = selected_country['WHO Region']
    temp_str = selected_region.to_string(index=False)
    extract_str = temp_str[1:]
    grp_temp = dodgeInput.groupby('WHO Region').get_group(extract_str)
    grp_temp = grp_temp.drop(columns=['iso_code'])
    death_list = []
    recovered_list = []
    active_list = []
    country_list = []
    for name, group in grp_temp.iteritems():
        if name == 'Deaths':
            death_list = group.tolist()
        elif name == 'Recovered':
            recovered_list = group.tolist()
        elif name == 'Active':
            active_list = group.tolist()
        elif name == 'WHO Region':
            region_list = group.tolist()  # Not Needed
        elif name == 'Country/Region':
            country_list = group.tolist()
        else:
            break
    lists = ['active_list', 'recovered_list', 'death_list']

    data = {'country_list': country_list[:7],
            'death_list': death_list[:7],
            'recovered_list': recovered_list[:7],
            'active_list': active_list[:7]}

    source = ColumnDataSource(data=data)

    continentBarPlot = figure(x_range=country_list[:7], y_axis_type="log", plot_height=500, plot_width=1200, title="continentBarPlot",
                              toolbar_location=None, tools="hover", tooltips="@country_list")

    continentBarPlot.vbar(x=dodge('country_list',  0.25, range=continentBarPlot.x_range), bottom=0.01, top='active_list', width=0.2, source=source,
                          color="#e84d60", legend_label="Active Cases")
    continentBarPlot.vbar(x=dodge('country_list',  0.0,  range=continentBarPlot.x_range), bottom=0.01, top='recovered_list', width=0.2, source=source,
                          color="#718dbf", legend_label="Recovered")
    continentBarPlot.vbar(x=dodge('country_list', -0.25, range=continentBarPlot.x_range), bottom=0.01, top='death_list', width=0.2, source=source,
                          color="#c9d9d3", legend_label="Deaths")

    continentBarPlot.title.text = 'Selected Country - %s' % (
        selectedCountryName)
    continentBarPlot.x_range.range_padding = 0.1
    continentBarPlot.xgrid.grid_line_color = None
    continentBarPlot.y_range.start = 10 ** 0
    continentBarPlot.y_range.end = 10 ** 6
    continentBarPlot.legend.location = "top_right"
    continentBarPlot.legend.orientation = "vertical"
    continentBarPlot.xaxis.axis_label = 'Country'

    hover = HoverTool(
        tooltips=[('Active ', '@active_list'), ('Recovered', '@recovered_list'), ('Dead', '@death_list')])
    continentBarPlot.add_tools(hover)

    if not isInit:
        # clear line plot from current document
        mainLayout = curdoc().get_model_by_name('mainLayout')
        mainLayoutChild = mainLayout.children
        row3 = curdoc().get_model_by_name('row3')
        mainLayoutChild.remove(row3)
        # bar plot is added here just to maintain the layout order
        mainLayoutChild.append(row(continentBarPlot, name='row3'))


def handleTap(model):
    global selectedCountryName
    global selectedCountryIsoCode

    selectedCountryName = findCountry((model.y, model.x))
    selectedCountryIsoCode = geoDataFrame[geoDataFrame['country']
                                          == selectedCountryName]['iso_code'].values[0]
    # TODO: change line plot and bar plot here
    barPlotCountryTotalCases(selectedCountryIsoCode,
                             selectedCountryName, getSelectorParam())
    piePlotForCountry(selectedCountryIsoCode, selectedCountryName)
    linePlotCountryTotalCases(selectedCountryIsoCode,
                              selectedCountryName, getSelectorParam())
    barPlotForContinent(selectedCountryIsoCode, selectedCountryName)
    # print(selectedCountryIsoCode)


selectOptions = ['Total Cases', 'Total Deaths',
                 'Total Cases Per Million', 'Total Deaths Per Million']
selector = Select(value=selectOptions[0], options=selectOptions)
selector.on_change('value', handleSelectorChange)
geoPlot.on_event(Tap, handleTap)

# initialize the geoPlot
init()
