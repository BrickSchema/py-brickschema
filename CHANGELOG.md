# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project is pre-1.0: breaking changes are released in a MINOR version bump.

Releases before 0.8.0 are not covered here; see the
[commit history](https://github.com/BrickSchema/py-brickschema/commits/master)
for those.

## [0.8.0] - 2026-09-14

First stable release since 0.7.9. This is a breaking release: it changes the
default Brick version and the default SHACL engine, and removes the
Allegrograph reasoner along with several pieces of long-broken surface area.

Identical in content to 0.8.0a1. (0.7.10a1 was published from an intermediate
state and is superseded by this release.)

### Removed

- **The Allegrograph OWL-RL backend**, along with the `[allegro]` extra and the
  `docker` dependency. It ran `agtool materialize` inside a
  `franzinc/agraph:v7.1.0` container to provide a third implementation of a
  profile the two in-process reasoners already cover.
  `expand("owlrl", backend="allegrograph")` now raises `ValueError`.
- **`brickschema.topquadrant_shacl`** and the bundled TopQuadrant CLI (49 MB of
  Java, including two 9 MB fat jars). Nothing imported the module;
  `brick-tq-shacl` ships its own copy of the engine. The wheel drops from
  8.2 MB to 1.3 MB as a result.
- **The `brick_validate` command.** It imported a `brickschema.validate` module
  that does not exist, and declared no console-script entry point, so it could
  neither be installed nor run.
- **`docs/requirements.txt`**, which was committed `uv export` output. Docs
  dependencies now come from the `docs` dependency group.

### Changed

- **The default Brick version is now 1.5** (was 1.4). `Graph()` and
  `GraphCollection()` load Brick 1.5 unless given `brick_version=`.
- **The default SHACL engine is now `shifty`**, falling back to `topquadrant`
  then `pyshacl`. Previously the order put `topquadrant` first. Inference and
  validation results may differ. Select explicitly with
  `validate(engine=...)` / `compile(engine=...)`.
- **`validate()` no longer modifies the graph.** It previously ran `compile()`
  as a side effect, and only for the pyshacl engine.
- **`validate()` and `compile()` raise `ValueError` for an unknown engine**
  instead of returning `None`.
- **`compile(extra_graphs=[...])` no longer merges those graphs into the
  model.** They drive inference; only inferred triples are added.
- **`expand()` always returns `self`.** It previously returned `None` for the
  `rdfs` profile and for `+`-joined profiles, which broke chaining.
- **`reasonable` and `pyshifty` are now base dependencies**, so the default
  OWL-RL backend and SHACL engine work on a plain `pip install brickschema`.
  The `[reasonable]` and `[shifty]` extras remain as empty aliases so existing
  install commands keep resolving.
- **Dependency cleanup**: dropped `requests` (never imported), moved
  `pyontoenv` to the dev group (used only by the test suite) and
  `importlib-resources` to `[brickify]`; dropped `alembic` and `six` from
  `[persistence]`, where they were already transitive.
- **`__version__` is read from package metadata.** It was hardcoded `"0.2.0"`.
- **Importing `brickschema` no longer calls `logging.basicConfig()`** or prints
  to stdout, so it no longer reconfigures the root logger of the importing
  application.
- Minimum Python is 3.11. The README and docs previously claimed 3.6, 3.7 and
  3.8 in various places.

### Added

- **`brickschema.shacl`** — the SHACL engine dispatch layer, exposing
  `available_engines()`, `resolve()`, `infer()` and `validate()`. `infer()`
  returns only newly inferred triples and never mutates its inputs.
- **The `brickify` console script.** It was documented in the README and
  `docs/brickify/` but no entry point was ever declared, so
  `pip install brickschema[brickify]` provided no command.
- **The `brickschema[all]` extra.** It was referenced by the README and three
  documentation pages but never existed, so `pip install brickschema[all]`
  installed nothing extra.
- Package metadata: project URLs, trove classifiers and keywords. `homepage`
  had been declared using a Poetry key that hatchling silently ignores, so the
  published package carried no links, classifiers or keywords at all.

### Fixed

- **`compile(engine="shifty")` corrupted the graph.** shifty round-trips its
  result through N-Triples, which relabels every blank node, so the diff
  against the input reported every blank-node triple as new and grafted a
  relabeled duplicate into the graph on each call. Brick is full of blank
  nodes, so a 77-triple graph grew to 126, 216 then 396 across three compiles.
  The graph is skolemized before inference, as the other engines already did,
  and `compile()` is now idempotent and matches pyshacl exactly.
- **`GraphCollection.remove_graph()` recursed infinitely** — it called itself.
- **`get_extensions()`** used `str.strip(".ttl")`, which strips a set of
  characters rather than a suffix, and emitted a spurious empty entry.
- **`Graph.load_file(source=...)` could only ever try one format.** rdflib
  closes the stream on a failed parse, so the ttl/n3/xml fallback failed with
  "I/O operation on closed file".
- **`expand("vbis")` raised `FileNotFoundError` on any 1.4 or 1.5 graph**, and
  `TagInferenceSession` failed for 1.4. `vbis-masterlist.csv` and
  `taglookup.pickle` are not packaged for every Brick version; both now fall
  back to the newest packaged copy.
- **`TagInferenceSession(rebuild_tag_lookup=True)` wrote `taglookup.pickle`
  into the caller's working directory** from its constructor. Use the new
  `save_tag_lookup()` to regenerate it deliberately.
- `VBISTagInferenceSession.expand()` raised `KeyError` for equipment whose
  class has no VBIS pattern.
- `orm.py` called `sys.exit(1)` at import time, and set `points` on generated
  classes so every instance of a Brick class shared one list.
- `merge.py` raised `UnboundLocalError` whenever every entity linked, and
  discarded its `merge_types` argument.
- `persistent.py` logged around ten `print()` calls from the commit path, and
  `version_before()` crashed when there was no earlier version.
- **The Read the Docs build.** It pinned Python 3.10 against
  `requires-python >=3.11`, so it could not install the package.

[0.8.0]: https://github.com/BrickSchema/py-brickschema/releases/tag/v0.8.0
[0.8.0a1]: https://github.com/BrickSchema/py-brickschema/releases/tag/v0.8.0a1
