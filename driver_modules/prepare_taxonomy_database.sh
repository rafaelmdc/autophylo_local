#!/bin/bash

prepare_taxonomy_database_version=1.0.0

. /data/config

input_dir=$1
out_dir=$2
prefix=$3

download=${download:-"false"}

# Define the URL and target directory
URL="https://ftp.ncbi.nlm.nih.gov/pub/taxonomy/new_taxdump/new_taxdump.tar.gz"
FILENAME="new_taxdump.tar.gz"

if [ -d "$out_dir" ]; then
    echo "The directory $out_dir already exists. Exiting."
    exit 1
else
    mkdir -p "$out_dir"
fi

int_folder="/data/${prefix}TaxonomyDatabase"
mkdir -p "$int_folder"

if [ "$download" != "download" ]; then
    if [ -d "/data/$input_dir" ]; then
        # Find the first file inside the directory $input_dir
        FILENAME=$(find "/data/$input_dir" -type f | head -n 1)
        
        if [ -n "$FILENAME" ]; then
            echo "Using file $FILENAME from directory /data/$input_dir."
            mv "$FILENAME" "$int_folder/$(basename "$FILENAME")"
        else
            echo "Error: No files found in directory /data/$input_dir."
            exit 1
        fi
    else
        echo "Error: /data/$input_dir is not a directory."
        exit 1
    fi
fi  # Closing the first if statement

# Check if the download option is set
if [ "$download" = "download" ]; then
    # If no file is provided, download from URL
    echo "No tar.gz file provided. Downloading from $URL..."
    FILENAME="$int_folder/new_taxdump.tar.gz"
    curl -o "$FILENAME" "$URL"

    # Check if the download was successful
    if [ $? -ne 0 ]; then
        echo "Failed to download the file."
        exit 1
    fi
    echo "Download complete."
fi

# Unpack specific files from the .tar.gz file
echo "Unpacking specific files"
tar -xzf "$FILENAME" -C "$int_folder" names.dmp nodes.dmp

if [ $? -ne 0 ]; then
    echo "Failed to unpack the specific files."
    exit 1
fi

echo "Converting to database."

mkdir /data/$out_dir

python3 prepare_taxonomy_database.py -id "$int_folder" -od "/data/$out_dir"

# Clean up: remove the downloaded .tar.gz file if it was downloaded by this script
if [ "$FILENAME" == "$int_folder/new_taxdump.tar.gz" ]; then
    rm "$FILENAME"
fi
