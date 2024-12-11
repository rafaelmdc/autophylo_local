import sqlite3
import os
import re
import argparse

class TaxonomyDatabase:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
    
    def find_rank_names(self, tax_id, ranks):
        current_tax_id = tax_id
        rank_names = {rank: "Name not found" for rank in ranks}

        while current_tax_id and ranks:
            self.cursor.execute("SELECT parent_tax_id, rank FROM nodes WHERE tax_id = ?", (current_tax_id,))
            result = self.cursor.fetchone()
            
            if result:
                parent_tax_id, rank_value = result
                if rank_value in ranks:
                    # Get the name from names table for this rank
                    self.cursor.execute("SELECT name_txt FROM names WHERE tax_id = ? AND name_class = 'scientific name'", (current_tax_id,))
                    name_result = self.cursor.fetchone()
                    if name_result:
                        rank_names[rank_value] = name_result[0]
                        ranks.remove(rank_value)  # Remove found rank from the list

                current_tax_id = parent_tax_id
            else:
                print(f"[Warning] Tax ID {current_tax_id} not found in nodes table.")
                break
        
        return rank_names
    
    def close(self):
        self.conn.close()

# Function to extract tax_id from filename
def extract_tax_id(filename):
    match = re.search(r'_(\d+)(?:\.[^.]+)?$', filename)
    return match.group(1) if match else None

def modify_fasta_headers(fasta_file, rank_names):
    """Generator that reads a FASTA file and modifies headers with the specified rank names."""
    rank_str = "_".join(rank_names.values()).replace(" ", "_")
    print(f"Processing file '{os.path.basename(fasta_file)}' with ranks: {rank_str}")
    
    # Format string for header lines with the rank as a variable
    header_format = ">{}_{}\n".format(rank_str, "{}")

    with open(fasta_file, "r") as file:
        while True:
            line = file.readline()
            if not line:
                break
            if line.startswith(">"):
                yield header_format.format(line.lstrip(">").strip())
            else:
                yield line

# Adjust the function to use buffered writing
def add_ranks_to_fasta_headers(main_dir, out_dir, db_file, ranks):
    os.makedirs(out_dir, exist_ok=True)
    db = TaxonomyDatabase(db_file)

    for file in os.listdir(main_dir):
        filepath = os.path.join(main_dir, file)
        tax_id = extract_tax_id(file)
        
        if tax_id:
            rank_names = db.find_rank_names(tax_id, ranks[:])  # Pass a copy of ranks
            new_filepath = os.path.join(out_dir, file)

            buffer = []
            for line in modify_fasta_headers(filepath, rank_names):
                buffer.append(line)
                
                if len(buffer) >= 1000:
                    with open(new_filepath, "a") as outfile:
                        outfile.writelines(buffer)
                    buffer = []

            if buffer:
                with open(new_filepath, "a") as outfile:
                    outfile.writelines(buffer)
        else:
            print(f"[Warning] Tax ID not found in filename: {file}")

    db.close()

if __name__ == '__main__':
    valid_ranks = ["species", "genus", "family", "order", "class", "phylum", "kingdom"]

    parser = argparse.ArgumentParser(description='Add multiple taxonomic ranks to FASTA headers.')
    parser.add_argument("-id", "--input_directory", help="Directory containing input files", required=True)
    parser.add_argument("-od", "--output_directory", help="Directory for output files", required=True)
    parser.add_argument("-db", "--database_file", help="Path to SQLite database file", required=True)
    parser.add_argument("-r", "--rank", help="Comma-separated list of taxonomic ranks to add.", required=True)
    args = parser.parse_args()

    # Parse the ranks into a list and validate each rank
    ranks = [rank.strip().lower() for rank in args.rank.split(",")]
    if not all(rank in valid_ranks for rank in ranks):
        print(f"[Error] Invalid ranks provided. Valid ranks are: {', '.join(valid_ranks)}")
        exit(1)

    add_ranks_to_fasta_headers(args.input_directory, args.output_directory, args.database_file, ranks)
