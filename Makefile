.PHONY: test docs

test:
	poetry run pytest -s -vvvv -n auto tests/

docs: docs/requirements.txt
	poetry run sphinx-apidoc -f -o docs/source brickschema
	cd docs && poetry run make html

docs/requirements.txt: pyproject.toml
	poetry export -f requirements.txt --output docs/requirements.txt
