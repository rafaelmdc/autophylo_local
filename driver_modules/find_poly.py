import argparse
import os
import re
import csv
import logging


def setup_logging(log_file="logfile.log"):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def log(message):
    logging.info(message)


class Match:
    """Defines a series of variables that contain information about the match sequence object."""

    def __init__(
        self, match, amino_acid, fasta_id=str, fasta_seq=str, nucsequence=str
    ) -> None:
        self.match_object = match
        self.fasta_id = fasta_id
        self.fasta_seq = fasta_seq
        self.length = match.span()[1] - match.span()[0]
        self.sequence = match.group()
        self.break_id, self.break_index = self.get_non_q_index(amino_acid)
        self.nucsequence = nucsequence

        # handles break formatting
        if self.break_index:
            after_break_size = int(self.length) - int(self.break_index)
            self.match_break = f"{amino_acid}{int(self.break_index) - 1}{self.break_id}{amino_acid}{after_break_size}_{match.span()[0]}to{match.span()[1]}"
        else:
            self.match_break = (
                f"{amino_acid}{self.length}_{match.span()[0]}to{match.span()[1]}"
            )

        # handles name
        try:
            acession_pattern = r"\[protein=([^\]]+)\]"
            acession_match = re.search(acession_pattern, fasta_id)
            if acession_match:
                self.name = acession_match.group(1)
            else:
                self.name = "None"
        except AttributeError:
            self.name = "None"

        # tries to find gene ID, if not found, stops the script.
        self.geneid = self.find_gene_id(fasta_id)
        if not self.geneid:
            raise SystemExit(
                f"{fasta_id} has no GeneID, cannot continue, exiting the script."
            )

    def get_non_q_index(self, amino_acid):
        """Returns index and character of a non-Q match if found"""
        non_qmatch = re.search(f"[^{amino_acid}]", self.sequence)
        if non_qmatch:
            return non_qmatch.group(), str(non_qmatch.start() + 1)
        return None, None

    @staticmethod
    def find_gene_id(sequence_data):
        geneid_pattern = r"GeneID:(\d+)"
        match = re.search(geneid_pattern, sequence_data)
        return match.group(1) if match else None


class Fasta:
    @staticmethod
    def parse_generator(fasta_input_path):
        """simple fasta file reader"""
        with open(fasta_input_path, "r") as file:
            sequence_id = None
            sequence_data = []

            for line in file:
                line = line.strip()
                if line.startswith(">"):
                    if sequence_id is not None:
                        yield sequence_id, "".join(sequence_data)
                    sequence_id = line
                    sequence_data = []
                else:
                    sequence_data.append(line)
            if sequence_id is not None:
                yield sequence_id, "".join(sequence_data)  # Yield the last sequence


class Poly:
    """Handles the matching of polys and sorting them into diferent outputs."""

    def __init__(self, input_dir, output_dir, input_basename, amino_acid, i):
        log(f"Finding poly chains in {input_basename}.")

        self.amino_acid = amino_acid
        self.fasta = Fasta()
        self.protein_dir = os.path.join(args.output_directory, "translate_out")
        self.output_dir = output_dir
        self.protein_file_path = os.path.join(protein_dir, input_basename)
        self.input_dir = input_dir
        self.nucleotide_file_path = os.path.join(input_dir, input_basename)
        self.csv_writers = {}

        ensure_directory_exists(os.path.join(output_dir, "reports_no_isoforms"))
        self.report_file_path = os.path.join(
            output_dir,
            "reports_no_isoforms",
            f"{os.path.splitext(input_basename)[0]}_{i}.csv",
        )

        ensure_directory_exists(os.path.join(output_dir, "reports"))
        self.report_file_path_normal = os.path.join(
            output_dir, "reports", f"{os.path.splitext(input_basename)[0]}_{i}.csv"
        )

        ensure_directory_exists(os.path.join(output_dir, "matches_protein"))
        self.output_file_path = os.path.join(
            output_dir,
            "matches_protein",
            f"{os.path.splitext(input_basename)[0]}_{i}.fasta",
        )

        ensure_directory_exists(os.path.join(output_dir, "matches_nucleotide"))
        self.output_nucleotide_file_path = os.path.join(
            output_dir,
            "matches_nucleotide",
            f"{os.path.splitext(input_basename)[0]}_{i}.fasta",
        )

        self.taxonomy = re.search(r".*_([^_]+ae)_.*", input_basename).group(1)

    def find_matches(self, pattern, header, sequence, nucsequence):
        matches = pattern.finditer(sequence)
        return [
            Match(match, self.amino_acid, header, sequence, nucsequence)
            for match in matches
        ]

    def create_csv_report(self, match, csv_writer):
        """Writes the match information to a CSV file."""
        row = [
            f"{match.fasta_id.strip()} [{match.match_break}]",
            match.name,
            match.match_object.start() + 1,
            match.sequence,
            match.length,
            match.match_break,
            match.fasta_seq,
            match.nucsequence,
            self.taxonomy,
        ]
        csv_writer.writerow(row)

    def append_to_output(self, output_file, matches, sequence):
        """Appends fasta match (header and poly info) information to the output file."""
        breaks = [x.match_break for x in matches]
        output_file.write(
            f"{matches[0].fasta_id.strip()} [poly={'_'.join(breaks)}]\n{sequence}\n"
        )

    def post_match(self, matches, writer_name):
        for match in matches:
            self.create_csv_report(match, self.csv_writers[writer_name])

    def process_lines(self):
        """Processes lines in the data file, finds matches, and writes to report and output files."""
        protein_generator = self.fasta.parse_generator(self.protein_file_path)
        nucleotide_generator = self.fasta.parse_generator(self.nucleotide_file_path)
        log(f"Nucleotide file path = {self.nucleotide_file_path}")
        log(f"Protein file path: {self.protein_file_path}")

        seen_gene_ids = {}  # Dictionary to track the largest protein for each Gene ID

        for (prot_id, prot_sequence), (nuc_id, nuc_sequence) in zip(
            protein_generator, nucleotide_generator
        ):
            # Find matches for the current protein sequence
            matches = self.find_matches(PATTERN, prot_id, prot_sequence, nuc_sequence)

            if matches:  # Proceed only if matches are found
                self.append_to_output(self.output_file, matches, prot_sequence)
                self.append_to_output(
                    self.output_nucleotide_file, matches, nuc_sequence
                )
                self.post_match(matches, "isoform")
                gene_id = matches[0].geneid  # Use the first match to get the Gene ID

                # Check if the Gene ID is already seen or if the current protein is larger
                if gene_id not in seen_gene_ids:
                    # If it's a new Gene ID, store the current protein and its details
                    seen_gene_ids[gene_id] = {
                        "protein_id": prot_id,
                        "nucleotide_sequence": nuc_sequence,
                        "matches": matches,
                    }
                else:
                    # If we've seen this Gene ID, compare lengths
                    current_largest = seen_gene_ids[gene_id]
                    if len(nuc_sequence) > len(current_largest["nucleotide_sequence"]):
                        # Update to the larger protein sequence
                        seen_gene_ids[gene_id] = {
                            "protein_id": prot_id,
                            "nucleotide_sequence": nuc_sequence,
                            "matches": matches,
                        }

        # Write only the largest proteins to output files
        log(
            f"{len(seen_gene_ids)} gene matches in {os.path.basename(self.nucleotide_file_path)}"
        )
        for gene_id, data in seen_gene_ids.items():
            self.post_match(data["matches"], "no_isoform")

    def create_csv_file(self, writer_name, report_file):
        self.csv_writers[writer_name] = csv.writer(report_file)
        self.csv_writers[writer_name].writerow(
            [
                "Fasta ID",
                "Seq Name",
                "Match Start",
                "Full sequence",
                "Length",
                "Sequence",
                "rootseq",
                "nucseq",
                "taxonomy",
            ]
        )

    def process_file(self):
        with open(self.protein_file_path, "r") as data_file, open(
            self.report_file_path, "w", newline=""
        ) as report_file, open(self.output_file_path, "w") as self.output_file, open(
            self.output_nucleotide_file_path, "w"
        ) as self.output_nucleotide_file, open(
            self.report_file_path_normal, "w"
        ) as isoform_report_file:

            self.create_csv_file("isoform", isoform_report_file)
            self.create_csv_file("no_isoform", report_file)
            self.process_lines()


if __name__ == "__main__":

    def ensure_directory_exists(path):
        """Checks if directory exists, if not, creates it."""
        if not os.path.exists(path):
            os.makedirs(path)

    # Makes code usable by CLI
    parser = argparse.ArgumentParser(description="Protein poly identifier.")
    parser.add_argument(
        "-id",
        "--input_directory",
        help="Directory containing input files",
        required=True,
    )
    parser.add_argument(
        "-od", "--output_directory", help="Directory for output files", required=True
    )
    parser.add_argument(
        "-aa",
        "--poly_amino_acid",
        help="The aminoacid of chosen poly chain",
        required=True,
    )
    parser.add_argument(
        "-s",
        "--size",
        help="The minimum size of the poly chain for positive flag",
        required=True,
    )
    parser.add_argument(
        "-b",
        "--break_poly",
        help="Allow a single aminoacid break in the desired homorepeat",
        required=True,
        default=True,
        choices=["True", "true", "False", "false"],
    )
    args = parser.parse_args()

    setup_logging(log_file=os.path.join(args.output_directory, "logfile.log"))

    if args.break_poly.capitalize() == "True":
        PATTERN = re.compile(
            r"{0}{{{1},}}([^{0}]{0}+)?".format(args.poly_amino_acid, args.size)
        )
    else:
        PATTERN = re.compile(r"{0}{{{1},}}".format(args.poly_amino_acid, args.size))

    protein_dir = os.path.join(args.output_directory, "translate_out")

    try:
        input_filenames = os.listdir(protein_dir)

    except FileNotFoundError:
        raise FileNotFoundError(f"Invalid input directory: {protein_dir}")

    for i, input_basename in enumerate(input_filenames):
        print(f"File: {input_basename}")
        poly = Poly(
            args.input_directory,
            args.output_directory,
            input_basename,
            args.poly_amino_acid,
            i,
        )
        poly.process_file()
