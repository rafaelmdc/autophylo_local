import requests, sys, csv, re, argparse, time

class Fasta:
    @staticmethod
    def parse_generator(fasta_input_path):
        """simple fasta file reader"""
        with open(fasta_input_path, "r") as file:
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
                yield sequence_id, ''.join(sequence_data)  # Yield the last sequence

class GetID:
    def __init__(self, input_path, output_path):
        self.fasta = Fasta()
        self.input_path = input_path
        self.output_path = output_path

    @staticmethod
    def find_gene_id(sequence_data):
        geneid_pattern = r"GeneID:(\d+)"  
        match = re.search(geneid_pattern, sequence_data) 
        return match.group(1) if match else None 
    
    def write_ids(self):
        with open(self.output_path, "w") as output_file:
            sequence_generator = self.fasta.parse_generator(self.input_path)
            ids = []
            for (nuc_id, nuc_sequence) in sequence_generator:
                gene_id = self.find_gene_id(nuc_id)
                if gene_id and gene_id not in ids:
                    ids.append(gene_id)
                    output_file.write(gene_id + "\n")

class RetrieveFasta:
    def __init__(self, input_path, output_path, data_path, premature_path):
        self.base_url = "https://www.ebi.ac.uk/proteins/api/proteins/"
        self.input_path = input_path
        self.output_path = output_path
        self.data_path = data_path
        self.premature_path = premature_path
        print("Generated retrieve fasta")

    def get_url(self, protein_id):
        return f"{self.base_url}{protein_id}"

    def get_missing_fasta(self, gene_id):
        gene_id_full = f"GeneID:{gene_id}"
        print(f"Trying to find {gene_id_full}")
        with open(self.data_path.rstrip(".tsv"), "r") as data_file, \
            open(self.premature_path.rstrip(".tsv"), "a") as premature_file:
            sequences = []
            found_line = False
            for line in data_file:
                if gene_id_full in line:
                    print(f"Found {gene_id} in {line}")
                    header = line
                    found_line = True
                    continue
                if found_line:
                    sequence = line
                    sequences.append((header,sequence))
                    found_line = False
            longest_sequence = max(sequences, key=lambda x: len(x[1]))
            print(f"Longest sequence is {longest_sequence}")
            premature_file.write(f"{longest_sequence[0]}{longest_sequence[1]}")

    def id_generator(self):
        with open(self.input_path) as file:
            tsv_file = csv.reader(file, delimiter="\t")
            for line in tsv_file:
                if line[1] in ["Not found"]:
                    print(f"{line[0]} not found")
                    self.get_missing_fasta(line[0])
                if len(line) > 1 and line[1] not in ["Not found", "UniProtKB"]:
                    yield line[1]

    def generate_fasta(self):
        with open(self.output_path.rstrip(".tsv"), "w") as self.output_file:
            protein_ids = self.id_generator()
            for protein_id in protein_ids:
                print(f"Retrieving {protein_id} from UniProt")
                requestURL = self.get_url(protein_id=protein_id)
                try:
                    r = requests.get(requestURL, headers={ "Accept" : "text/x-fasta"}, timeout=10)
                    r.raise_for_status()
                    responseBody = r.text
                    self.output_file.write(responseBody)

                    # Throttle the requests to avoid exceeding the API rate limit
                    time.sleep(0.005)

                except requests.exceptions.RequestException as e:
                    print(f"Error retrieving {protein_id}: {e}")

class ExtractRefseq:
    def __init__(self, input_path, output_path, data_path):
        self.input_path = input_path
        self.output_path = output_path
        self.data_path = data_path

    def extract_significant_alignment(self, file_obj):
        n = 0
        found_section = False
        for line in file_obj:
            if "Sequences producing significant alignments:" in line:
                found_section = True  # We found the section header, start reading lines after this
                continue 
            if found_section:
                line = line.strip()
                if not line:  # Skip the first empty line after the header
                    continue
                if line:  # If there's content, it's part of the significant alignments
                    n += 1
                    print(n)
                    found_section = False
                    yield line[:65]

    def find_sequence(self, alignment):
        with open(self.data_path, "r") as data_file:
            found_line = False
            print(f"Finding: {alignment}")
            for line in data_file:
                if alignment in line:
                    print(f"Found alignment")
                    header = line
                    found_line = True
                    continue
                if found_line:
                    return (header, line)

    def write_significant_alignments(self):
        with open(self.input_path, "r") as input_file, \
            open(self.output_path, "a") as output_file:
            
            alignment_generator = self.extract_significant_alignment(input_file)
            for alignment in alignment_generator:
                fasta_snippet = self.find_sequence(alignment)
                output_file.write(f"{fasta_snippet[0]}{fasta_snippet[1]}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve references, not made to work outside pipeline environment')
    parser.add_argument("-id", "--input_directory", help="Directory containing input files", required=True)
    parser.add_argument("-od", "--output_directory", help="Directory for output files", required=True)
    parser.add_argument("-bl", "--block_script", choices=['0', '1', '2'], help=argparse.SUPPRESS)
    parser.add_argument("-d_id", "--data_directory", required=False, help=argparse.SUPPRESS)
    parser.add_argument("-p_od", "--premature_output_directory", required=False, help=argparse.SUPPRESS)
    args = parser.parse_args()

    block_script = args.block_script
    if block_script == "0":
        # Gets IDs
        get_id = GetID(input_path=args.input_directory, output_path=args.output_directory)
        get_id.write_ids()

    if block_script == "1":
        # Handles not found sequences
        id_finder = RetrieveFasta(input_path=args.input_directory, 
                                  output_path=args.output_directory, 
                                  data_path=args.data_directory,
                                  premature_path=args.premature_output_directory)
        id_finder.generate_fasta()

    if block_script == "2":
        # Handles refseq IDs
        extraction = ExtractRefseq(input_path=args.input_directory, output_path=args.output_directory, data_path=args.data_directory)
        extraction.write_significant_alignments()