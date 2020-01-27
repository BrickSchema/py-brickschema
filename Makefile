.PHONY: test docs

test:
	pytest -s -vvvv tests/

docs:
	sphinx-apidoc -f -o docs/source brickschema
	cd docs && make html
