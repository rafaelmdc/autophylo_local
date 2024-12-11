import argparse
import os
import re

def parse_generator(file):
    """Simple FASTA file reader"""
    sequence_id = None
    sequence_data = []
    for line in file:
        line = line.strip()
        if line.startswith('>'):
            if sequence_id is not None:
                yield sequence_id, ''.join(sequence_data)
            sequence_id = line
            sequence_data = []
        else:
            sequence_data.append(line)
    if sequence_id is not None:
        yield sequence_id, ''.join(sequence_data)

def get_gene_id(header):
    pattern = r"\[gene=(.*?)\]"
    match = re.search(pattern, header)
    return match.group(1) if match else None

def get_protein_id(header):
    """Extracts a generic protein ID from the header"""
    parts = header.split('_')
    if len(parts) >= 3:
        return f"{parts[-3]}_{parts[-2]}"
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Add GeneID to FASTA headers")
    parser.add_argument("-id", "--input_directory", required=True, help="Directory with input FASTA files")
    parser.add_argument("-dd", "--data_directory", required=True, help="Directory with data files containing GeneIDs")
    parser.add_argument("-od", "--output_directory", required=True, help="Directory to save output files")
    args = parser.parse_args()

    for file_path in os.listdir(args.input_directory):
        file_name = os.path.basename(file_path)
        
        with open(os.path.join(args.input_directory, file_path), "r") as input_file, \
             open(os.path.join(args.data_directory, file_name), "r") as data_file, \
             open(os.path.join(args.output_directory, file_name), "w") as output_file:

            input_generator = parse_generator(input_file)
            data_generator = parse_generator(data_file)
            
            data_set = [item[0] for item in data_generator]  # Collect all headers from data file

            for input_item in input_generator:
                protein_id = get_protein_id(input_item[0]).strip()
                gene_id = None

                # Search for matching protein ID in data_set
                for item in data_set:
                    if protein_id in item:  # Corrected to check if protein_id is a substring of item
                        gene_id = get_gene_id(item)
                        break

                if gene_id is None:
                    exit(f"Missing geneID for protein ID {protein_id} in file {file_name}")

                output_header = f"{input_item[0].strip()} [GeneID={gene_id}]"
                output_file.write(f"{output_header}\n{input_item[1]}\n")
