#!/bin/bash

merge_autop_version=3.0.0
merge_seda_docker_version=1.6.0
merge_seda_program_version=1.6.0

find_poly_version=0

. /data/config

# Check if aminoacid is specified, otherwise return an error and exit
if [ -z "$aminoacid" ]; then
    echo "Error: Amino acid is not specified."
    exit 1
fi

removal=${removal:-true}
# capitalized for posterity, python will auto capitalize it.
break_poly=${break_poly:-True}

input_dir=$1
out_dir=$2
prefix=$3

if [ "$merge_seda_docker_c_version" != "" ]; then
    merge_autop_version="?"
    merge_seda_docker_version=$merge_seda_docker_c_version
    merge_seda_program_version="?"
fi

start=$(echo "docker run --rm  -v $dir:/data pegi3s/seda:$merge_seda_docker_version /opt/SEDA/run-cli.sh")

mkdir -p /data/$out_dir /data/${prefix}Annotate_Poly/translate_out

# Loop over files in /data/Data
for entry in /data/Data/*; do
    entry_name=$(basename "$entry")
    echo "File: $entry_name"
    docker run --rm -v $dir:/data pegi3s/emboss transeq -sequence /data/$input_dir/$entry_name -outseq "/data/${prefix}Annotate_Poly/translate_out/$entry_name" -trim
done

# Run poly_finder
echo "Identify poly chains"
python3 annotate_poly.py -id "/data/$input_dir" -od /data/${prefix}Annotate_Poly -aa "$aminoacid" -s "$size" -b $break_poly

if [ "$removal" = "true" ] ; then
    if [ -d "/data/${prefix}Annotate_Poly/translate_out" ]; then
        rm -r /data/${prefix}Annotate_Poly/translate_out
        echo "Deleted /data/${prefix}Annotate_Poly/translate_out"
    else
        echo "Directory /data/${prefix}Annotate_Poly/translate_out not found."
    fi
fi

for entry in /data/${prefix}Annotate_Poly/genome/*; do
    entry_name=$(basename "$entry")
    mv /data/${prefix}Annotate_Poly/genome/$entry_name /data/$out_dir/$entry_name
done