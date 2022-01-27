.PHONY: test docs

test:
	pytest -s -vvvv -n auto tests/

docs:
	poetry export -f requirements.txt --output docs/requirements.txt
	sphinx-apidoc -f -o docs/source brickschema
	cd docs && make html
