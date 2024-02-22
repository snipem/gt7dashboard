SHELL=/bin/bash -O expand_aliases

limited:
	GT7_LIMITED=true python3 gt7telemetry.py 192.168.178.120

race:
	BOKEH_LOG_LEVEL=fatal GT7_LIMITED=true GT7_HIDE_ANALYSIS=true GT7_HIDE_TUNING=true python3 gt7telemetry.py 192.168.178.120

normal:
	python3 gt7telemetry.py 192.168.178.120

doc:
	python3 generate_doc.py

deps:
	python3 -m pip install -r requirements.txt

test_deps:
	python3 -m pip install pytest

test: test_deps deps
	python3 -m pytest .

car_lists:
	python3 helper/download_cars_csv.py

serve:
	bokeh serve .

deploy:
	git push
	ssh ${MK_SERVER_USER}@${MK_SERVER_HOST} "cd work/gt7dashboard && git pull && git switch '$(shell git rev-parse --abbrev-ref HEAD)' && cd ~/git/conf/docker && sudo -S CONTAINER_NAME=gt7dashboard make build"
