from bokeh.plotting import figure, output_file, show
from bokeh.models import WheelZoomTool

# Output to an HTML file
output_file("line_plot_with_x_wheel_zoom.html")

# Create a figure object
p = figure(
        title="Simple Line Plot with X-Axis Wheel Zoom", 
        x_axis_label='X-Axis', 
        y_axis_label='Y-Axis'
        
        )

# Create a WheelZoomTool for x-axis only
wheel_zoom = WheelZoomTool(dimensions='width')

# Add the wheel zoom tool to the figure
p.add_tools(wheel_zoom)


# Set the created wheel_zoom tool as the active_scroll tool
p.toolbar.active_scroll = wheel_zoom

# Add a line renderer with legend and line thickness
p.line([1, 2, 3, 4, 5], [6, 7, 2, 4, 5], legend_label="Line", line_width=2)

# Show the results
show(p)
