import gt7dashboard.gt7help as gt7help

if __name__ == '__main__':

    out_markdown = "## Manual\n\n"

    out_markdown += "### Tab 'Get Faster'\n\n"

    out_markdown += "#### Speed Deviation (Spd. Dev.)\n\n"
    out_markdown += gt7help.SPEED_VARIANCE_HELP

    print(out_markdown)

    with open("README.md", 'r+') as f:
        content = f.read()
        pos = content.find('## Manual')
        if pos != -1:
            f.seek(pos)
            f.truncate()
            f.write(out_markdown)
