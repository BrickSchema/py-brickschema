.PHONY: test docs

test:
	pytest -s -vvvv -n auto tests/

docs: docs/requirements.txt
	sphinx-apidoc -f -o docs/source brickschema
	cd docs && make html

docs/requirements.txt: pyproject.toml
	poetry export -f requirements.txt --output docs/requirements.txt
