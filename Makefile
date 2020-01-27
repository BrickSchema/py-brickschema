.PHONY: test docs

test:
	pytest -s -vvvv tests/

docs:
	cd docs && make html
