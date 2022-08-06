limited:
	GT7_LIMITED=true python3 gt7telemetry.py 192.168.178.120

race:
	BOKEH_LOG_LEVEL=fatal GT7_LIMITED=true GT7_HIDE_ANALYSIS=true GT7_HIDE_TUNING=true python3 gt7telemetry.py 192.168.178.120

normal:
	python3 gt7telemetry.py 192.168.178.120

deps:
	pip3 install -r requirements
