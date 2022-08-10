from bokeh.plotting import figure, curdoc
from bokeh.driving import linear

import random

import gt7communication
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

curdoc().add_root(p)

# Add a periodic callback to be run every 500 milliseconds
curdoc().add_periodic_callback(update, 16)
