#!/bin/bash

alignment_directory=../brickschema/ontologies/1.2/alignments
extension_directory=../brickschema/ontologies/1.2/extensions
brick_branch=v1.2-release

set -ex
git clone --branch $brick_branch https://github.com/BrickSchema/Brick
pushd Brick
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
(. venv/bin/activate && make)
popd
alignments=$(find Brick/alignments -iname '*alignment.ttl')
mkdir -p $alignment_directory
cp $alignments $alignment_directory

mkdir -p $extension_directory
cp Brick/extensions/*.ttl $extension_directory
rm -rf Brick
