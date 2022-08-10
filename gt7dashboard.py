from typing import List

import pandas
from bokeh.plotting import figure, curdoc
from bokeh.driving import linear

from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, TableColumn, DataTable
from bokeh.layouts import layout
from bokeh.io import show
import pandas as pd

import gt7communication
from gt7helper import pd_data_frame_from_lap
from gt7lap import Lap
from gt7plot import get_session_layout

p = figure(plot_width=1000, plot_height=600)
r1 = p.line([], [], color="green", line_width=2)
r2 = p.line([], [], color="blue", line_width=2)
r3 = p.line([], [], color="red", line_width=2)

ds1 = r1.data_source
ds2 = r2.data_source
ds3 = r3.data_source

gt7comm = gt7communication.GT7Communication("192.168.178.120")
gt7comm.start()

source = ColumnDataSource(pd_data_frame_from_lap([]))

columns = [
    TableColumn(field='SubjectID', title='SubjectID'),
    TableColumn(field='Result_1', title='Result 1'),
    TableColumn(field='Result_2', title='Result 2'),
    TableColumn(field='Result_3', title='Result 3'),
    TableColumn(field='Result_4', title='Result 4'),
    TableColumn(field='Result_5', title='Result 5')
]


myTable = DataTable(source=source, columns=columns)

@linear()
def update_laps(step):
    # time, x, y, z = from_csv(reader).next()
    laps = gt7comm.get_laps()
    print("Adding %d laps" % len(laps))
    print(laps[0])
    myTable.source.data = ColumnDataSource.from_df(pd_data_frame_from_lap(laps))
    myTable.trigger('source', myTable.source, myTable.source)

@linear()
def update(step):
    # time, x, y, z = from_csv(reader).next()
    last_package = gt7comm.get_last_data()
    ds1.data['x'].append(last_package.package_id)
    ds2.data['x'].append(last_package.package_id)
    ds3.data['x'].append(last_package.package_id)
    ds1.data['y'].append(last_package.carSpeed)
    ds2.data['y'].append(last_package.throttle)
    ds3.data['y'].append(last_package.brake)
    ds1.trigger('data', ds1.data, ds1.data)
    ds2.trigger('data', ds2.data, ds2.data)
    ds3.trigger('data', ds3.data, ds3.data)

# l = get_session_layout(gt7comm.get_laps(), True)



# df = pd.DataFrame({
#     'SubjectID': ['Subject_01','Subject_02','Subject_03'],
#     'Result_1': ['Positive','Negative','Negative'],
#     'Result_3': ['Negative','Invalid','Positive'],
#     'Result_4': ['Positive','Negative','Negative'],
#     'Result_5': ['Positive','Positive','Negative']
# })

# show(myTable)

l = layout(children=[
    [p],
    [myTable]
])

curdoc().add_root(l)

# Add a periodic callback to be run every 500 milliseconds
curdoc().add_periodic_callback(update, 60) # best would be 16ms, 60ms is smooth enough
curdoc().add_periodic_callback(update_laps, 1000) # best would be 16ms, 60ms is smooth enough
