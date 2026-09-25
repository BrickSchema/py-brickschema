# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project is pre-1.0: breaking changes are released in a MINOR version bump.

Releases before 0.8.0 are not covered here; see the
[commit history](https://github.com/BrickSchema/py-brickschema/commits/master)
for those.

## [0.8.0] - 2026-09-25

First release since 0.7.9, and a breaking one: it changes the default Brick
version and the default SHACL engine, and removes the Allegrograph reasoner
along with several pieces of long-broken surface area. 0.8.0a1, 0.8.0a2 and
0.7.10a1 were pre-releases of this version; this entry covers all changes since
0.7.9.

### Removed

- **The Allegrograph OWL-RL backend**, along with the `[allegro]` extra and the
  `docker` dependency. It ran `agtool materialize` inside a
  `franzinc/agraph:v7.1.0` container to provide a third implementation of a
  profile the two in-process reasoners already cover.
  `expand("owlrl", backend="allegrograph")` now raises `ValueError`.
- **`brickschema.topquadrant_shacl`** and the bundled TopQuadrant CLI (49 MB of
  Java, including two 9 MB fat jars). Nothing imported the module;
  `brick-tq-shacl` ships its own copy of the engine. The wheel drops from
  8.2 MB to 1.4 MB as a result.
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
- **`compile()` with shifty writes inferred triples straight into the graph**
  using pyshifty's `in_place` inference, so the graph is not copied or diffed.
  On `GraphCollection` and `VersionedGraphCollection` they go to the default
  graph, and SQL-backed graphs take them in one store transaction.
- **`validate()` no longer modifies the graph.** It previously ran `compile()`
  as a side effect, and only for the pyshacl engine.
- **`validate()` and `compile()` raise `ValueError` for an unknown engine**
  instead of returning `None`.
- **`compile(extra_graphs=[...])` no longer merges those graphs into the
  model.** They drive inference; only inferred triples are added.
- **`expand()` always returns `self`.** It previously returned `None` for the
  `rdfs` profile and for `+`-joined profiles, which broke chaining.
- **`VersionedGraphCollection` changesets are atomic.** The changeset log,
  the graph writes and the precommit hooks run in one database transaction, so
  a failure rolls all of them back. `undo()` and `redo()` are atomic too, and
  changesets are written in batches rather than one statement per triple.
- **`VersionedGraphCollection`'s default graph is named
  `urn:x-rdflib:default`**, as for `Dataset`. It was a fresh BNode each time
  the store was opened, which the SQL store handed back as a `URIRef`.
- **`reasonable` and `pyshifty` (`>=0.5.0`) are now base dependencies**, so the
  default OWL-RL backend and SHACL engine work on a plain
  `pip install brickschema`. The `[reasonable]` and `[shifty]` extras remain as
  empty aliases so existing install commands keep resolving.
- **`[persistence]` requires `brickschema-rdflib-sqlalchemy>=0.7.1`** (was
  `>=0.6.1`), which adds the store transactions above. It no longer pulls in
  `alembic`, `mako` or `six`, and the floor excludes 0.6.2, which wrongly
  installed flake8, tox, pytest and setuptools as runtime dependencies.
- **Dependency cleanup**: dropped `requests` (never imported), moved
  `pyontoenv` to the dev group (used only by the test suite) and
  `importlib-resources` to `[brickify]`. A plain install is 12 packages, down
  from 18.
- **`__version__` is read from package metadata.** It was hardcoded `"0.2.0"`.
- **Importing `brickschema` no longer calls `logging.basicConfig()`** or prints
  to stdout, so it no longer reconfigures the root logger of the importing
  application.
- Minimum Python is 3.11. The README and docs previously claimed 3.6, 3.7 and
  3.8 in various places.

### Added

- **Brick 1.5**, with its BOT, REC and VBIS alignments and its 223P
  extensions.
- **`brickschema.shacl`** — the SHACL engine dispatch layer, exposing
  `available_engines()`, `resolve()`, `infer()`, `infer_in_place()` and
  `validate()`. `infer()` returns only newly inferred triples and never
  mutates its inputs; `infer_in_place()` adds them to the data graph. Each
  accepts one ontology/shape graph or a list of them.
- **The `brickify` console script.** It was documented in the README and
  `docs/brickify/` but no entry point was ever declared, so
  `pip install brickschema[brickify]` provided no command.
- **The `brickschema[all]` extra.** It was referenced by the README and three
  documentation pages but never existed, so `pip install brickschema[all]`
  installed nothing extra.
- **`TagInferenceSession.save_tag_lookup()`**, to regenerate
  `taglookup.pickle` deliberately.
- Package metadata: project URLs, trove classifiers and keywords. `homepage`
  had been declared using a Poetry key that hatchling silently ignores, so the
  published package carried no links, classifiers or keywords at all.

### Fixed

- **`GraphCollection.remove_graph()` recursed infinitely** — it called itself.
- **`GraphCollection.contexts()` raised `ValueError`** with rdflib's in-memory
  store: it checked contexts against brickschema's `Graph` class rather than
  `rdflib.Graph`.
- **`get_extensions()`** used `str.strip(".ttl")`, which strips a set of
  characters rather than a suffix, and emitted a spurious empty entry.
- **`Graph.load_file(source=...)` could only ever try one format.** rdflib
  closes the stream on a failed parse, so the ttl/n3/xml fallback failed with
  "I/O operation on closed file".
- **`expand("vbis")` raised `FileNotFoundError` on any 1.4 graph**, and
  `TagInferenceSession` failed for 1.4. `vbis-masterlist.csv` and
  `taglookup.pickle` are not packaged for every Brick version; both now fall
  back to the newest packaged copy.
- **`TagInferenceSession(rebuild_tag_lookup=True)` wrote `taglookup.pickle`
  into the caller's working directory** from its constructor. It now builds
  the lookup in memory; see `save_tag_lookup()`.
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
- The docs showed `expand("shacl")`, which was removed before 0.7.9; they now
  use `compile()`.

[0.8.0]: https://github.com/BrickSchema/py-brickschema/releases/tag/v0.8.0
