import bokeh.plotting as bplt
import pandas as pd

station_info = pd.read_csv('station_info.csv')
print(station_info.head())

source = ColumnDataSource(df)