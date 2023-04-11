import urllib.request

url = 'https://raw.githubusercontent.com/ddm999/gt7info/web-new/_data/db/cars.csv'
filename = 'db/cars.csv'

urllib.request.urlretrieve(url, filename)
