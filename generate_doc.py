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

    out_markdown += "#### Throttle\n\n"
    out_markdown += gt7help.THROTTLE_DIAGRAM + "\n\n"

    out_markdown += "#### Braking\n\n"
    out_markdown += gt7help.BRAKING_DIAGRAM + "\n\n"

    out_markdown += "#### Coasting\n\n"
    out_markdown += gt7help.COASTING_DIAGRAM + "\n\n"

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
