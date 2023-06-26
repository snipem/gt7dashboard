import gt7dashboard.gt7help as gt7help

if __name__ == '__main__':

    out_markdown = "## Manual\n\n"

    out_markdown += "### Tab 'Get Faster'\n\n"

    out_markdown += "#### Header\n\n"
    out_markdown += gt7help.HEADER + "\n\n"

    out_markdown += "#### Lap Controls\n\n"
    out_markdown += gt7help.LAP_CONTROLS + "\n\n"

    out_markdown += "#### Time / Diff\n\n"
    out_markdown += gt7help.TIME_DIFF + "\n\n"

    out_markdown += "#### Lap Controls\n\n"
    out_markdown += gt7help.LAP_CONTROLS + "\n\n"

    out_markdown += "#### Speed \n\n"
    out_markdown += gt7help.SPEED_DIAGRAM + "\n\n"

    out_markdown += "#### Race Line\n\n"
    out_markdown += gt7help.RACE_LINE_MINI + "\n\n"

    out_markdown += "#### Speed Deviation (Spd. Dev.)\n\n"
    out_markdown += gt7help.SPEED_VARIANCE + "\n\n"

    out_markdown += """I got inspired for this diagram by the [Your Data Driven Podcast](https://www.yourdatadriven.com/).
On two different episodes of this podcast both [Peter Krause](https://www.yourdatadriven.com/ep12-go-faster-now-with-motorsports-data-analytics-guru-peter-krause/) and [Ross Bentley](https://www.yourdatadriven.com/ep3-tips-for-racing-faster-with-ross-bentley/) mentioned this visualization.
If they had one graph it would be the deviation in the (best) laps of the same driver, to improve said drivers performance learning from the differences in already good laps. If they could do it once, they could do it every time.\n\n"""

    out_markdown += "#### Throttle\n\n"
    out_markdown += gt7help.THROTTLE_DIAGRAM + "\n\n"

    out_markdown += "#### Yaw Rate / Second\n\n"
    out_markdown += gt7help.YAW_RATE_DIAGRAM + "\n\n"

    out_markdown += "#### Braking\n\n"
    out_markdown += gt7help.BRAKING_DIAGRAM + "\n\n"

    out_markdown += "#### Coasting\n\n"
    out_markdown += gt7help.COASTING_DIAGRAM + "\n\n"

    out_markdown += "#### Gear\n\n"
    out_markdown += gt7help.GEAR_DIAGRAM + "\n\n"

    out_markdown += "#### RPM\n\n"
    out_markdown += gt7help.RPM_DIAGRAM + "\n\n"

    out_markdown += "#### Boost\n\n"
    out_markdown += gt7help.BOOST_DIAGRAM + "\n\n"

    out_markdown += "#### Tire Speed / Car Speed\n\n"
    out_markdown += gt7help.TIRE_DIAGRAM + "\n\n"

    out_markdown += "#### Time Table\n\n"
    out_markdown += gt7help.TIME_TABLE + "\n\n"

    out_markdown += "#### Fuel Map\n\n"
    out_markdown += gt7help.FUEL_MAP + "\n\n"

    out_markdown += "#### Tuning Info\n\n"
    out_markdown += gt7help.TUNING_INFO + "\n\n"

    out_markdown += "### Tab 'Race Line'\n\n"

    out_markdown += gt7help.RACE_LINE_BIG + "\n\n"

    print(out_markdown)

    with open("README.md", 'r+') as f:
        content = f.read()
        pos = content.find('## Manual')
        if pos != -1:
            f.seek(pos)
            f.truncate()
            f.write(out_markdown)
