lint:
	poetry run flake8 sanic_json_logging tests examples
	poetry run black -l 120 .
	poetry run isort --profile black --line-length 120 .
	poetry run mypy sanic_json_logging

test: flake
	poetry run pytest

doc:
	make -C docs html
	@echo "open file://`pwd`/docs/_build/html/index.html"

.PHONY: lint test doc
