import sqlite3
import os
import re
import argparse
import shutil  # Import shutil for file moving

class TaxonomyDatabase:
    def __init__(self, db_file):
        print("Loading database.")
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.wanted_tax_id = []

    def find_taxid(self, name):
        self.cursor.execute("SELECT tax_id FROM names WHERE name_txt = ?", (name,))
        results = self.cursor.fetchall()
        if results:
            self.wanted_tax_id = [row[0] for row in results]
            print(f"Found wanted_id: {self.wanted_tax_id}")
        else:
            exit(f"No taxID found for {name}")

    def check_match(self, tax_id):
        if tax_id is None:
            return False  # Handle case where tax_id is None

        current_tax_id = tax_id
        while current_tax_id:
            self.cursor.execute("SELECT parent_tax_id FROM nodes WHERE tax_id = ?", (current_tax_id,))
            result = self.cursor.fetchone()
            
            if result:
                parent_tax_id = result[0]  # Unpack the tuple to get the actual parent_tax_id
                if parent_tax_id in self.wanted_tax_id:
                    return True
                current_tax_id = parent_tax_id
            else:
                return False
        return False

class FileManagment:
    def __init__(self, input_path, output_path, contaminated_path):
        self.search_pattern = r'_(\d+)(?:\.[^.]+)?$'
        self.input_path = input_path
        self.output_path = output_path
        self.contaminated_path = contaminated_path

    def extract_tax_id(self, file_name):
        match = re.search(self.search_pattern, file_name)
        return match.group(1) if match else None
    
    def move_to_output(self, file_name):
        shutil.copy(os.path.join(self.input_path, file_name), os.path.join(self.output_path, file_name))

    def move_to_contaminated(self, file_name):
        shutil.copy(os.path.join(self.input_path, file_name), os.path.join(self.contaminated_path, file_name))

if __name__ == '__main__':
    # CLI argument parser setup
    parser = argparse.ArgumentParser(description='Classify files based on taxonomy ID.')
    parser.add_argument("-id", "--input_directory", help="Directory containing input files", required=True)
    parser.add_argument("-od", "--output_directory", help="Directory for output files", required=True)
    parser.add_argument("-db", "--database_file", help="Path to SQLite database file", required=True)
    parser.add_argument("-tn", "--taxonomy_name", help="Taxonomy rank name string.", required=True)
    args = parser.parse_args()

    taxonomy_manager = TaxonomyDatabase(args.database_file)
    file_manager = FileManagment(args.input_directory, os.path.join(args.output_directory, "passed"), os.path.join(args.output_directory, "contamination"))
    
    taxonomy_manager.find_taxid(args.taxonomy_name.capitalize())
    
    for file in os.listdir(args.input_directory):
        file_name = os.path.basename(file)
        tax_id = file_manager.extract_tax_id(file_name=file_name)

        if taxonomy_manager.check_match(tax_id=tax_id):
            file_manager.move_to_output(file_name=file_name)
        else:
            print(f"File {file_name} is contamination.")
            file_manager.move_to_contaminated(file_name=file_name)
