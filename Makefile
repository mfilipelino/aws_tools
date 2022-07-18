venv:
	python3.9 -m venv venv


install:
	venv/bin/pip install -r requirements.txt


build: venv install


tests:
	venv/bin/python -m unittest discover -s src -p '*_test.py'

clean:
	rm -rf venv