import pandas as pd


data = pd.read_csv('datasets/owid-covid-data.csv').groupby(['location'], as_index=False).sum()
# data = np.genfromtxt('datasets/owid-covid-data.csv', delimiter=';', dtype=np.str)

tData = data.loc[data['location'].isin(['India'])]

print(tData['new_deaths']) 

print(data.dtypes)