import pandas as pd
import numpy as np
import holoviews as hv
import bokeh.plotting as plt
from holoviews import opts
hv.extension('bokeh')

station_info = pd.read_csv('station_info.csv')
print(station_info.head())

scatter = hv.Scatter(station_info, 'services', 'ridership')
fig = hv.render(scatter)
plt.show(fig)