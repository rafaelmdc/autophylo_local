#!/bin/bash

data_retrieve_version=1.0.0

. /data/config

input_dir=$1
out_dir=$2
prefix=$3

if [ -z "$taxonomy_name" ]; then
    echo "No taxonomy name in config"
    exit 1 
fi

echo "Starting $taxonomy_name download."

mkdir -p /data/"$prefix"DatasetsDownload

docker run --rm -v $dir:/data pegi3s/ncbi-datasets datasets download genome taxon $taxonomy_name --annotated --assembly-level chromosome,complete --assembly-source RefSeq --include cds --dehydrated --filename /data/${prefix}DatasetsDownload/download.zip

unzip /data/"$prefix"DatasetsDownload/download.zip -d /data/"$prefix"DatasetsDownload/ && rm /data/"$prefix"DatasetsDownload/download.zip

for item in /data/"$prefix"DatasetsDownload/*; do
    if [ "$(basename "$item")" != "ncbi_dataset" ]; then
        rm -rf "$item"
    fi
done

docker run --rm -v $dir:/data pegi3s/ncbi-datasets datasets rehydrate --directory /data/"$prefix"DatasetsDownload/

echo Finished Download

main_dir="/data/"$prefix"DatasetsDownload/ncbi_dataset/data"
report_path="$main_dir"/assembly_data_report.jsonl

n=0

if [ ! -d "$main_dir" ]; then
    echo "Directory $main_dir does not exist."
    exit 1
fi

if [ ! -f "$report_path" ]; then
    echo "File $report_path does not exist."
    exit 1
fi

get_taxID() {
    local accession="$1"
    local report="$2"
    local taxID=""

    while IFS= read -r line; do
        if [[ $line == *"\"accession\":\"$accession\""* ]]; then
            # Use grep to find the first instance of "taxId" and stop there
            taxID=$(echo "$line" | grep -o '"taxId": *[0-9]*' | head -n 1 | grep -o '[0-9]*')
            break
        fi
    done < "$report"
    echo "$taxID"
}

process_directory() {
    local dir="$1"
    local prefix="$2"
    local taxID
    taxID=$(get_taxID "$prefix" "$report_path")

    if [ -z "$taxID" ]; then
        echo "taxID not found for $prefix"
        return
    fi

    for item in "$dir"/*; do
        if [ -f "$item" ]; then
            ((n++))
            filename=$(basename "$item")
            name_without_extension="${filename%.*}"
            extension="${filename##*.}"
            new_file="${dir}/${name_without_extension}_${prefix}_${taxID}.${extension}"
            mv "$item" "$new_file"
        
        elif [ -d "$item" ]; then
            ((n++))
            dir_name=$(basename "$item")
            new_dir="${dir}/${dir_name}_${prefix}_${taxID}"
            mv "$item" "$new_dir"
            process_directory "$new_dir" "$prefix"
        fi
    done
}

echo Beggining file formating
for folder in "$main_dir"/*; do
    if [ -d "$folder" ]; then
        folder_name=$(basename "$folder")
        process_directory "$folder" "$folder_name"
    fi
done

mkdir -p /data/$out_dir

# Moving files to the output_dir
for processed_folder in "$main_dir"/*; do
    if [ -d "$processed_folder" ]; then
        for item in "$processed_folder"/*; do
            mv "$item" "/data/$out_dir"
        done
        rm -r "$processed_folder"
    fi
done

echo "$n files downloaded."
