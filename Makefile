.PHONY: black black-test check clean clean-build clean-pyc clean-test coverage dist dockerfile dockerfile-canary dockerfile-push docs flake8 gen-ci help install lint prepare pylint pylint-quick pyre release rename servedocs test test-all tox
define BROWSER_PYSCRIPT
import os, webbrowser, sys
try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT
BROWSER := python -c "$$BROWSER_PYSCRIPT"
VERSION := `cat VERSION`
package := "gmail2s3"

help:
	@echo "clean - remove all build, test, coverage and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "clean-test - remove test and coverage artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "test-all - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "docs - generate Sphinx HTML documentation, including API docs"
	@echo "release - package and upload a release"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"

clean: clean-build clean-pyc clean-test

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +
	find . -name '.mypy_cache' -exec rm -fr {} +
	find . -name '.pyre' -exec rm -fr {} +
clean-test:
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/

test:
	poetry run py.test --cov=$(package) --junitxml=junit/test-results.xml --cov-report=html --cov=com --cov-report=xml --cov-report=term-missing  --verbose tests

test-all:
	poetry run py.test --cov=$(package) --junitxml=junit/test-results.xml --cov-report=html--cov=com --cov-report=xml --cov-report=term-missing  --verbose tests

coverage:
	poetry run coverage run --source $(package) setup.py test
	poetry run coverage report -m
	poetry run coverage html
	$(BROWSER) htmlcov/index.html

docs: install
	rm -f test1
	poetry run  sphinx-apidoc  -f -P -o docs/test1 $(package)
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(BROWSER) docs/_build/html/index.html

servedocs: docs
	watchmedo shell-command -p '*.rst' -c '$(MAKE) -C docs html' -R -D .

release: clean
	python setup.py sdist upload
	python setup.py bdist_wheel upload

dist: clean
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

install: clean
	poetry install

pylint-quick:
	poetry run pylint --rcfile=.pylintrc $(package)  -E -r y

pylint:
	poetry run pylint --rcfile=".pylintrc" $(package)

dockerfile: clean
	docker build -t img.conny.dev/connylabs/gmail2s3:v$(VERSION) .

dockerfile-canary: clean
	docker build -t img.conny.dev/connylabs/gmail2s3:canary .
	docker push img.conny.dev/connylabs/gmail2s3:canary

dockerfile-push: dockerfile
	docker push img.conny.dev/connylabs/gmail2s3:v$(VERSION)

gen-ci:
	ffctl gen

check: pylint black-test

pyre:
	poetry run pyre

black:
	poetry run black -t py310 conf tests $(package)

black-test:
	poetry run black -t py310 conf tests $(package) --check

rename:
	ack GMAIL2S3 -l | xargs -i{} sed -r -i "s/GMAIL2S3/\{\{cookiecutter.varEnvPrefix\}\}/g" {}
	ack gmail2s3 -l | xargs -i{} sed -r -i "s/gmail2s3/\{\{cookiecutter.project_slug\}\}/g" {}
	ack Gmail2S3 -l | xargs -i{} sed -r -i "s/Gmail2S3/\{\{cookiecutter.baseclass\}\}/g" {}
