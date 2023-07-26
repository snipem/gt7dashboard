FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# This is a bug in bokeh: https://github.com/bokeh/bokeh/issues/13170
# FIXME remove me later
ENV BOKEH_RESOURCES=cdn

ADD https://raw.githubusercontent.com/ddm999/gt7info/web-new/_data/db/cars.csv db/cars.csv
RUN chmod -R 755 db

CMD [ "bokeh", "serve", "." ]
