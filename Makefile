SHELL := /bin/bash
code := jgutils
include .vscode/.env

.PHONY : format
format:  ## autopep, isort, ruff
	@uv run --frozen autopep8 --recursive --in-place $(code)
	@uv run --frozen isort $(code)
	@uv run --frozen ruff check $(code)

.PHONY : lint
lint:  ## ruff linting
	@uv run --frozen ruff check $(code)
