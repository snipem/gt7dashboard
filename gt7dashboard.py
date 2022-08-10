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
from gt7helper import secondsToLaptime
from gt7lap import Lap
from gt7plot import get_session_layout

def pd_data_frame_from_lap(laps: List[Lap], best_lap: int) -> pd.core.frame.DataFrame:
    df = pd.DataFrame()
    for lap in laps:
        time_diff = ""
        if best_lap == lap.LapTime:
            # lap_color = 35 # magenta
            # TODO add some formatting
            pass
        elif lap.LapTime < best_lap: # LapTime cannot be smaller than bestlap, bestlap is always the smallest. This can only mean that lap.LapTime is from an earlier race on a different track
            time_diff = "-"
        elif best_lap > 0:
            time_diff = secondsToLaptime(-1 * (best_lap / 1000 - lap.LapTime / 1000))

        df = df.append({'number':lap.Number,
                        'time':secondsToLaptime(lap.LapTime / 1000),
                        'diff':time_diff,
                        'fullthrottle':lap.FullThrottleTicks/lap.LapTicks,
                        'throttleandbreak':lap.ThrottleAndBrakesTicks/lap.LapTicks,
                        'fullbreak':lap.FullBrakeTicks/lap.LapTicks,
                        'nothrottle':lap.NoThrottleNoBrakeTicks/lap.LapTicks,
                        'tyrespinning':lap.TiresSpinningTicks/lap.LapTicks,
                        },
                       ignore_index=True)

    return df

p = figure(plot_width=1000, plot_height=600)
r1 = p.line([], [], color="green", line_width=2)
r2 = p.line([], [], color="blue", line_width=2)
r3 = p.line([], [], color="red", line_width=2)

ds1 = r1.data_source
ds2 = r2.data_source
ds3 = r3.data_source

gt7comm = gt7communication.GT7Communication("192.168.178.120")
gt7comm.start()

source = ColumnDataSource(pd_data_frame_from_lap([], best_lap=gt7comm.session.best_lap))

columns = [
    TableColumn(field='number', title='#'),
    TableColumn(field='time', title='Time'),
    TableColumn(field='diff', title='Diff'),
    TableColumn(field='fullthrottle', title='Full Throttle'),
    TableColumn(field='fullbreak', title='Full Break'),
    TableColumn(field='nothrottle', title='No Throttle'),
    TableColumn(field='tyrespinning', title='Tire Spin')
]


myTable = DataTable(source=source, columns=columns)


@linear()
def update_laps(step):
    # time, x, y, z = from_csv(reader).next()
    laps = gt7comm.get_laps()
    print("Adding %d laps" % len(laps))
    myTable.source.data = ColumnDataSource.from_df(pd_data_frame_from_lap(laps, best_lap=gt7comm.session.best_lap))
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
