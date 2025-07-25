.PHONY: test docs

test:
	uv run pytest -s -vvvv -n auto tests/

docs: docs/requirements.txt
	uv run sphinx-apidoc -f -o docs/source brickschema
	cd docs && uv run make html

docs/requirements.txt: pyproject.toml
	uv export --no-hashes --format requirements-txt > docs/requirements.txt
