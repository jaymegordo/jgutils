SHELL := /bin/bash
code := jgutils

.PHONY : format
format:  ## run autopep, ruff
	@uv run --frozen autopep8 --recursive --in-place $(code)
	@uv run --frozen ruff check $(code) --select I001 --fix --quiet
	@uv run --frozen ruff check $(code) --quiet

.PHONY : lint
lint:  ## ruff linting
	@uv run --frozen ruff check $(code)
