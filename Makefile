.PHONY: test docs

test:
	pytest -s -vvvv tests/

docs:
	pdoc3 --html -o docs --force brickschema
