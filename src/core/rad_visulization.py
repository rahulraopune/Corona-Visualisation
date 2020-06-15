from os.path import dirname, join
import pandas as pandaRef
import matplotlib.pyplot as plt
from pandas.plotting import radviz
import plotly.express as plotlybar

#Global Variables 
DATASETNAME = 'owid-covid-data.csv'
SUBDIRECTORYNAME = 'datasets'

#
# Read the DATASETNAME CSV file and create a DataFrame
#
def readCSVFileData(subDirectoryName, dataSetName):
    
    dataFrameRef = pandaRef.read_csv(join(dirname(__file__), subDirectoryName, dataSetName))
    return dataFrameRef

#
# Clean the DataFrame for continental Vis, remove redundant tuples 
#
def cleanDataFrame_continentalVis(dataFrameRef):

    # drop World data and drop iso_code with NaN values
    dataFrameRef = dataFrameRef[dataFrameRef.iso_code != 'OWID_WRL']

    # Add new Year/Month Col and formatted the Year-Month-Day date field to Year/Month
    dataFrameRef['Year/Month'] = pandaRef.to_datetime(dataFrameRef['date']).apply(lambda x: '{year}/{month}'.format(year=x.year, month=x.month))
    # sort by date in descending
    dataFrameRef = dataFrameRef.sort_values(by='date', ascending=False)

    dataFrameRef = dataFrameRef[['Year/Month', 'continent', 'location', 'total_cases', 'total_deaths', 'population']]
    return dataFrameRef

#
# Clean the DataFrame for Top 10 Country Vis, remove redundant tuples 
#
def cleanDataFrame_Top10Country(dataFrameRef):
    
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
    uniqueDataFrame = uniqueDataFrame.sort_values(by='total_cases', ascending=False)
    uniqueDataFrame = uniqueDataFrame.head(20)

    top20country = uniqueDataFrame['location']

    top20DataFrame = dataFrameRef['location'].isin(top20country)
    #print(dataFrameRef[top20DataFrame])
    return dataFrameRef[top20DataFrame]


#
# TotalCases for continental Vis vs Total Cases Reported
#
def barVisulization_continental_totalcases(dataFrameRef):

    selectCol = dataFrameRef[['continent','total_cases', 'total_deaths', 'population', 'location', 'Year/Month']]
    #selectCol = selectCol.sort_values(by='total_cases', ascending=True)
    fig = plotlybar.bar(selectCol, x='total_cases', y='continent', color='Year/Month', orientation='h', hover_data=['total_cases'], height=1000, title="COVID-19  Continent Vs Total Cases Reported")
    fig.show()

#
# TotalCases for continental Vis vs Deaths
#
def barVisulization_continental_fatalities(dataFrameRef):

    selectCol = dataFrameRef[['continent','total_cases', 'total_deaths', 'population', 'location', 'Year/Month']]
    #selectCol = selectCol.sort_values(by='total_deaths', ascending=True)
    fig = plotlybar.bar(selectCol, x='total_deaths', y='continent', color='Year/Month', orientation='h', hover_data=['total_deaths'], height=1000, title="COVID-19  Continent Vs Fatalities Reported")
    fig.show()

#
# TotalCases for Top 20 Country Vis vs Total Cases Reported
#
def barVisulization_top20Country_totalcases(dataFrameRef):

    selectCol = dataFrameRef[['continent','total_cases', 'total_deaths', 'population', 'location', 'Year/Month']]
    #selectCol = selectCol.sort_values(by='total_cases', ascending=True)
    fig = plotlybar.bar(selectCol, x='total_cases', y='location', color='Year/Month', orientation='h', hover_data=['total_cases'], height=1000, title="COVID-19  Top 20 Country Vs Total Cases Reported")
    fig.show()

#
# TotalCases for Top 20 Country Vis vs Fatalities Reported
#
def barVisulization_top20Country_totaldeaths(dataFrameRef):

    selectCol = dataFrameRef[['continent','total_cases', 'total_deaths', 'population', 'location', 'Year/Month']]
    #selectCol = selectCol.sort_values(by='total_deaths', ascending=True)
    fig = plotlybar.bar(selectCol, x='total_deaths', y='location', color='Year/Month', orientation='h', hover_data=['total_deaths'], height=1000, title="COVID-19  Top 20 Country Vs Fatalities Reported")
    fig.show()

def mainFunction():
    dataFrameRef = readCSVFileData(SUBDIRECTORYNAME, DATASETNAME)

    covidDataFrame_continentalVis = cleanDataFrame_continentalVis(dataFrameRef)

    barVisulization_continental_totalcases(covidDataFrame_continentalVis)

    barVisulization_continental_fatalities(covidDataFrame_continentalVis)

    covidDataFrame_Top10Country = cleanDataFrame_Top10Country(dataFrameRef)

    barVisulization_top20Country_totalcases(covidDataFrame_Top10Country)

    barVisulization_top20Country_totaldeaths(covidDataFrame_Top10Country)

mainFunction()
