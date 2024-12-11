#!/bin/bash
echo "Started find_poly"

merge_autop_version=3.0.0
merge_seda_docker_version=1.7.1
merge_seda_program_version=1.7.1

Find_Poly_version=0

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

mkdir -p /data/$out_dir /data/${prefix}Find_Poly/translate_out

# Loop over files in /data/Data
for entry in /data/$input_dir/*; do
    entry_name=$(basename "$entry")
    #docker run --rm -v $dir:/data pegi3s/emboss transeq -sequence /data/$input_dir/$entry_name -outseq "/data/${prefix}Find_Poly/translate_out/$entry_name" -trim
    python3 translate.py /data/$input_dir/$entry_name /data/${prefix}Find_Poly/translate_out/$entry_name
    echo "Finished translating: $entry_name"
done

# Run poly_finder
echo "Identify poly chains"
python3 find_poly.py -id "/data/$input_dir" -od /data/${prefix}Find_Poly -aa "$aminoacid" -s "$size" -b $break_poly

if [ "$removal" = "true" ] ; then
    if [ -d "/data/${prefix}Find_Poly/translate_out" ]; then
        rm -r /data/${prefix}Find_Poly/translate_out
        echo "Deleted /data/${prefix}Find_Poly/translate_out"
    else
        echo "Directory /data/${prefix}Find_Poly/translate_out not found."
    fi
fi

for entry in /data/${prefix}Find_Poly/matches_nucleotide/*; do
    entry_name=$(basename "$entry")
    cp /data/${prefix}Find_Poly/matches_nucleotide/$entry_name /data/$out_dir/$entry_name
done

mkdir /data/files_to_keep/poly_reports

for entry in /data/${prefix}Find_Poly/reports_no_isoforms/*; do
    entry_name=$(basename "$entry")
    cp $entry /data/files_to_keep/poly_reports/$entry_name
done

