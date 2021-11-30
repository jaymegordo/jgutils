SHELL := /bin/bash
code := jgutils
include .vscode/.env

.PHONY : format
format:  ## autopep, isort, flake
	@poetry run autopep8 --recursive --in-place $(code)
	@poetry run isort $(code)
	@poetry run flake8 $(code)

.PHONY : flake
flake:  ## run flake with only selected dirs
	@poetry run flake8 $(code)

.PHONY : publish
publish:  ## publish to pypi - NOTE doesnt work, cant have git deps (eg pygments)
	@poetry publish -u ${PYPI_USERNAME} -p ${PYPI_PASSWORD}