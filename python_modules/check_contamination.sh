#!/bin/bash

check_contamination=1.0.0

. /data/config

input_dir=$1
out_dir=$2
prefix=$3

echo "Checking for contamination."

mkdir -p /data/$out_dir
mkdir -p /data/"$prefix"CheckContamination
mkdir  /data/"$prefix"CheckContamination/passed
mkdir  /data/"$prefix"CheckContamination/contamination

python3 check_contamination.py -id /data/$input_dir -od /data/"$prefix"CheckContamination -db $taxonomy_database -tn $contamination_taxonomy

cp -v /data/"$prefix"CheckContamination/passed/* /data/$out_dir
