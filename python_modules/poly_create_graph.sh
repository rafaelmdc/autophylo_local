#!/bin/bash

merge_autop_version=3.0.0
merge_seda_docker_version=1.7.1
merge_seda_program_version=1.7.1

Find_Poly_version=0

. /data/config

input_dir=$1
out_dir=$2
prefix=$3


if [ "$merge_seda_docker_c_version" != "" ]; then
    merge_autop_version="?"
    merge_seda_docker_version=$merge_seda_docker_c_version
    merge_seda_program_version="?"
fi

mkdir /data/$out_dir 

python3 poly_create_graph.py -id /data/$input_dir -od /data/$out_dir/ -rd /data/files_to_keep/poly_reports/