#!/bin/bash

brick_directory=brickschema/ontologies/1.4
alignment_directory=${brick_directory}/alignments
extension_directory=${brick_directory}/extensions
brick_branch=master

set -ex

# generate Brick from recent checkout, along with extensions + alignments
git clone --branch $brick_branch https://github.com/BrickSchema/Brick
pushd Brick
git submodule update --init --recursive
uv run make
popd

# copy alignments in
alignments=$(find Brick/alignments -iname '*alignment.ttl')
mkdir -p $alignment_directory
cp $alignments $alignment_directory

# copy extensions in
mkdir -p $extension_directory
cp Brick/extensions/*.ttl $extension_directory

# update Brick
cp Brick/Brick.ttl $brick_directory
rm -rf Brick
