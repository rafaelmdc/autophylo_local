#!/bin/bash

add_taxonomy_version=1.0.0

. /data/config

input_dir=$1
out_dir=$2
prefix=$3

data_dir=${data_dir:-"ncbi_data"}

echo "Adding Gene_id"

python3 add_gene_id.py -id /data/$input_dir -od /data/$out_dir -dd /data/$data_dir
