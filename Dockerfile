FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ADD https://raw.githubusercontent.com/ddm999/gt7info/web-new/_data/db/cars.csv db/cars.csv
RUN chmod -R 755 db

CMD [ "python3", "gt7dashboard.py"]
