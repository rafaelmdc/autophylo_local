#!/bin/bash

merge_autop_version=3.0.0
merge_seda_docker_version=1.6.0
merge_seda_program_version=1.6.0

wich_reference_version=0

. /data/config

input_dir=$1
out_dir=$2
prefix=$3

echo "Extracting GeneID"
mkdir -p /data/$out_dir /data/${prefix}Wich_Reference/gene_ids
for entry in /data/$input_dir/*; do
    entry_name=$(basename "$entry")
    python3 wich_reference.py -id "/data/$input_dir/$entry_name" -od /data/${prefix}Wich_Reference/gene_ids/$entry_name --block_script 0
done

cp -r /data/$input_dir /data/${prefix}Wich_Reference/database

echo "Converting GeneID to UniProtKD"
mkdir -p /data/$out_dir /data/${prefix}Wich_Reference/uniprot_ids
for entry in /data/${prefix}Wich_Reference/gene_ids/*; do
   entry_name=$(basename "$entry")
   docker run --rm -v $dir:/data -w /data pegi3s/id-mapping gene-id-to-uniprotkb /data/${prefix}Wich_Reference/gene_ids/$entry_name /data/${prefix}Wich_Reference/uniprot_ids/$entry_name.tsv
done

echo "Retrieving UniProtKD sequences"
mkdir -p /data/$out_dir /data/${prefix}Wich_Reference/uniprot_fasta
for entry in /data/${prefix}Wich_Reference/uniprot_ids/*; do
   entry_name=$(basename "$entry")
   python3 wich_reference.py -id "/data/${prefix}Wich_Reference/uniprot_ids/$entry_name" -od /data/${prefix}Wich_Reference/uniprot_fasta/$entry_name --block_script 1 -d_id /data/${prefix}Wich_Reference/database/$entry_name -p_od /data/$out_dir/$entry_name
done

mkdir /data/${prefix}Wich_Reference/blast_out
for entry in /data/${prefix}Wich_Reference/uniprot_fasta/*; do
    entry_name=$(basename "$entry")
    docker run --rm -v $dir:/data pegi3s/blast makeblastdb -in /data/${prefix}Wich_Reference/database/$entry_name -dbtype nucl -parse_seqids
    docker run --rm -v $dir:/data pegi3s/blast tblastn -query /data/${prefix}Wich_Reference/uniprot_fasta/$entry_name -db /data/${prefix}Wich_Reference/database/$entry_name -evalue 0.05 -out /data/${prefix}Wich_Reference/blast_out/$entry_name
done

echo "Retrieving highest score sequences"
for entry in /data/${prefix}Wich_Reference/blast_out/*; do
   entry_name=$(basename "$entry")
   python3 wich_reference.py -id "/data/${prefix}Wich_Reference/blast_out/$entry_name" -od /data/$out_dir/$entry_name --block_script 2 -d_id /data/$input_dir/$entry_name
done