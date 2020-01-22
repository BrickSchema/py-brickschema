#!/bin/bash
old_version=$1
new_version=$2

sed -i -e "s/$old_version/$new_version/g" brickschema/__init__.py
sed -i -e "s/$old_version/$new_version/g" pyproject.toml
sed -i -e "s/$old_version/$new_version/g" tests/test_brickschema.py
