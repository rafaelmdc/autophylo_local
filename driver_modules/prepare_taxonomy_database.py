import sqlite3
import argparse
import os

def create_database_from_dmp(nodes_dmp="nodes.dmp", names_dmp="names.dmp", db_file="taxonomy.db"):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Drop existing tables if they exist
    cursor.execute("DROP TABLE IF EXISTS nodes")
    cursor.execute("DROP TABLE IF EXISTS names")

    # Create tables for nodes and names
    cursor.execute("""
        CREATE TABLE nodes (
            tax_id INTEGER PRIMARY KEY,
            parent_tax_id INTEGER,
            rank TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE names (
            tax_id INTEGER,
            name_txt TEXT,
            unique_name TEXT,
            name_class TEXT,
            PRIMARY KEY (tax_id, name_txt, name_class)
        )
    """)

    # Load nodes.dmp into nodes table
    with open(nodes_dmp, "r") as file:
        for line in file:
            fields = line.strip().split("\t|\t")
            tax_id = int(fields[0].strip())
            parent_tax_id = int(fields[1].strip())
            rank = fields[2].strip()
            cursor.execute("INSERT INTO nodes (tax_id, parent_tax_id, rank) VALUES (?, ?, ?)", 
                           (tax_id, parent_tax_id, rank))

    # Load names.dmp into names table
    with open(names_dmp, "r") as file:
        for line in file:
            fields = line.strip().split("\t|\t")
            tax_id = int(fields[0].strip())
            name_txt = fields[1].strip()
            unique_name = fields[2].strip() if fields[2].strip() else None
            name_class = fields[3].replace("|", "").strip()
            cursor.execute("INSERT INTO names (tax_id, name_txt, unique_name, name_class) VALUES (?, ?, ?, ?)",
                           (tax_id, name_txt, unique_name, name_class))

    # Commit and create indexes to speed up queries
    conn.commit()
    cursor.execute("CREATE INDEX idx_nodes_tax_id ON nodes (tax_id)")
    cursor.execute("CREATE INDEX idx_names_tax_id ON names (tax_id)")
    conn.commit()
    conn.close()
    print("[DEBUG] SQLite database created from .dmp files.")

if __name__ == '__main__':
    # Valid ranks to check against the database
    valid_ranks = ["species", "genus", "family", "order", "class", "phylum", "kingdom"]

    # CLI argument parser setup
    parser = argparse.ArgumentParser(description='Add family taxonomy to FASTA headers.')
    parser.add_argument("-id", "--input_directory", help="Directory containing input files", required=True)
    parser.add_argument("-od", "--output_directory", help="Directory for output files", required=True)
    args = parser.parse_args()

    nodes_path = os.path.join(args.input_directory, "nodes.dmp")
    names_path = os.path.join(args.input_directory, "names.dmp")
    taxonomy_path = os.path.join(args.output_directory, "taxonomy.db")

    # Example usage
    create_database_from_dmp(nodes_path, names_path, taxonomy_path)
