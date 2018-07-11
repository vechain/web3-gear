.PHONY: clean-pyc clean-build

help:
	@echo "clean - remove build artifacts & Python file artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "release - package and upload a release"
	@echo "sdist - package"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

release: clean
	python3 setup.py sdist bdist_wheel
	twine upload -r pypi dist/*

sdist: clean
	python3 setup.py sdist bdist_wheel
	ls -l dist
