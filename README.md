# Poly Warehouse
## Table of Contents

- [About](#about)
- [Usage](#description)

---

## About

### Overview
Local "branch" of the autophylo pipeline focused on locating and extacting information of homorepeats with brief usage documentation and descriptions.


---

## Description
All variables for the config are in bold.

### add_gene_id
If found, adds the gene ID present in the fasta header to the file name, enabling the usage of the discombobulate operation without losing the geneID information.

### add_taxonomy_local
Adds the specified **rank**, specified in the config file from the following options:
- species
- genus
- family
- order
- class
- phylum
- kingdom

Requires a local ncbi taxonomy database copy to ensure no network and API issues, the **path** to the database must be specified in the config as **taxonomy_database** (will probably change this).

variables: rank, taxonomy_database

### annotate_poly
From a given number of input fasta files finds the specified poly **aminoacid** and minimum **size***. By default, it will permit any 1 aminoacid break in the polyQ sequences, this can be disabled by adding **break_poly** as false to the config file.

> If aminoacid=Q, size=5 and break_poly was not specified, the string QQQQAQQ, will be flagged as positive, since it has >5 Q's and only one aminoacid break.

If the given sequence has a a poly match, it will append the relevant data to the header.

The module needs to translate nucleotide sequences, by default it will delete this translated file, an optional parameter **removal** can be set to false to disable this behaviour. 

>variables: aminoacid, size, break_poly,removal

### check_contamination
From a given **contamination_taxonomy** finds it's ID in a local ncbi **taxonomy_database** (path to the database) and checks it against the file taxon, _*if and only if*_ the taxon ID is specified in the name (can be done by add_taxonomy).
Non matching IDs will not be in the output folder, instead they will be inside the "contamination" folder.

>variables: contamination_taxonomy, taxonomy_database

### data_retrieve
From a specified **taxonomy_name** downloads to the output folder every ncbi complete genome and chromossome refseq dataset with the matching taxon.

>variables: taxonomy_name

### find_poly
From a given number of input fasta files finds the specified poly **aminoacid** and **minimum size***. By default, it will permit any 1 aminoacid break in the polyQ sequences, this can be disabled by adding **break_poly** as false to the config file.
This module differs from annotate_poly since, the output folder only the matching sequences will be present and, it will also generate two .csv spreadheets, one with only non-isoform data and one with every match data. These spreadsheets will be added to files to keep for posterity.

It is **very important** to note, in order for this module to work, **add_taxonomy** needs to have been run, since it relies on the information to generate the spreadsheet data. (this can be changed to be a variable, is it worth it?)

Currently it only accepts family names for automatic taxon generation.

>variables: aminoacid, size, break_poly, removal

### poly_create_graph
After running a find_poly, the user can add poly_create_graph to the pipeline. This module will take the data from the former and generate relevant graphs.
Currently it only accepts family names for automatic taxon generation.
Those being:

- Appearences per protein (and log)
- Average length of the poly
- The starting point in % 
- CAG-CAA relations (in polyQ case) (and log)

### prepare_taxonomy_database
The module will download, unpack and convert the ncbi taxonomy database dump into a functional local sql3 database, that can be used by other modules, or by the user.

### wich reference
The wich_reference module will attempt to find the UniprotKB reference for each sequence in fasta file in the input folder, this way removing all but one reference isoform. If no matching ID is found, it will the biggest base sequence as reference.
It relies on the GeneID being present on the header, so it should be used before any discombobulate operation.

### boxplot_generation
Boxplot generation currently cannot be directly accessed by the user, but the module contains everything needed to generate dynamic and or custom boxplots with minimal effort.