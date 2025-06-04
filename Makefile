venv:
	python3.9 -m venv venv


install:
	venv/bin/pip install -r requirements.txt


build: venv install

.PHONY: tests
tests:
	venv/bin/python -m unittest discover -s tests -p '*_test.py'

clean:
	rm -rf venv