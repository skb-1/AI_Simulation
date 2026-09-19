.PHONY: install run test test-all demo build clean

install:
	pip install -e ./matrixholo && pip install -e ./aicreator

run:
	python -m aicreator

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
