.PHONY: install run gui desktop test test-all demo build clean

install:
	pip install -e ./matrixholo && pip install -e ./aicreator

run:
	python main.py

gui:
	python main.py --gui --port 8000

desktop:
	python main.py --desktop

test:
	pytest matrixholo/tests

test-all:
	pytest matrixholo/tests aicreator/tests

demo:
	matrixholo --demo

build:
	python -m build ./matrixholo && python -m build ./aicreator

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build dist
