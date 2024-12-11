#!/bin/bash

add_taxonomy_version=1.0.0

. /data/config

input_dir=$1
out_dir=$2
prefix=$3

echo "Adding taxonomy"

if [ -z "$taxonomy_database" ]; then
    echo "Please specify a database path in the pipeline config."
    exit 1
fi

if [ -z "$rank" ]; then
    echo "Please specify ranks in the database config from [species, genus, family, order, class, phylum, kingdom]"
    exit 1
fi

rank_list=("species" "genus" "family" "order" "class" "phylum" "kingdom")

# Convert the comma-separated ranks to an array
IFS=',' read -r -a ranks <<< "$rank"

# Check if all specified ranks are valid
all_valid=true
for item in "${ranks[@]}"; do
    item=$(echo "$item" | tr '[:upper:]' '[:lower:]')  # Ensure case-insensitivity
    if [[ ! " ${rank_list[@]} " =~ " $item " ]]; then
        echo "[Error] '$item' is not a valid rank. Valid ranks are: ${rank_list[*]}"
        all_valid=false
    fi
done

# If all ranks are valid, proceed; otherwise, exit
if [ "$all_valid" = true ]; then
    mkdir -p /data/$out_dir
    python3 add_taxonomy.py -id /data/$input_dir -od /data/$out_dir -db $taxonomy_database -r "$rank"
else
    echo "[Error] One or more ranks provided are invalid. Exiting."
    exit 1
fi
