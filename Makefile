code := jgutils

.PHONY : format
format:  ## autopep, isort, flake
	@poetry run autopep8 --recursive --in-place $(code)
	@poetry run isort $(code)
	@poetry run flake8 $(code)

.PHONY : flake
flake:  ## run flake with only selected dirs
	@poetry run flake8 $(code)