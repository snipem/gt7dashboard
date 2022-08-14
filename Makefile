SHELL=/bin/bash -O expand_aliases

limited:
	GT7_LIMITED=true python3 gt7telemetry.py 192.168.178.120

race:
	BOKEH_LOG_LEVEL=fatal GT7_LIMITED=true GT7_HIDE_ANALYSIS=true GT7_HIDE_TUNING=true python3 gt7telemetry.py 192.168.178.120

normal:
	python3 gt7telemetry.py 192.168.178.120

deps:
	pip3 install -r requirements

serve:
	GT7_PLAYSTATION_IP=192.168.178.120 bokeh serve gt7dashboard.py

deploy:
	git push
	ssh ${MK_SERVER_HOST} "cd work/gt7telemetry; git pull; cd ~/git/conf/docker; sudo -S CONTAINER_NAME=gt7telemetry make build"

