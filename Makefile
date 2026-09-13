.PHONY: test docs sync lock build clean

# xdist's -n auto spawns one worker per core; on an 8-core machine those eight
# concurrent Brick loads plus the TopQuadrant JVM have been observed to get a
# worker killed ("node down: Not properly terminated"). Override if you like,
# e.g. PYTEST_ARGS="-n auto" or PYTEST_ARGS="" for a serial run.
PYTEST_ARGS ?= -n 4

sync:
	uv sync --all-extras --dev

lock:
	uv lock

test:
	uv run pytest -s -vvvv $(PYTEST_ARGS)

build:
	uv build

docs:
	uv run --group docs sphinx-apidoc -f -o docs/source brickschema
	cd docs && uv run --group docs make html

clean:
	rm -rf dist docs/_build
