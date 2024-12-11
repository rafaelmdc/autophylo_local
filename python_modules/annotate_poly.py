import argparse
import os
import re


def ensure_directory_exists(path):
    """Checks if directory exists, if not, creates it."""
    if not os.path.exists(path):
        os.makedirs(path)


class Match:
    """Defines a series of variables that contain information about the match sequence object."""

    def __init__(self, match, amino_acid, fasta_id=str, fasta_seq=str) -> None:
        self.match_object = match
        self.fasta_id = fasta_id
        self.fasta_seq = fasta_seq
        self.length = match.span()[1] - match.span()[0]
        self.sequence = match.group()
        self.break_id, self.break_index = self.get_non_q_index(amino_acid)

        if self.break_index:
            after_break_size = int(self.length) - int(self.break_index)
            self.match_break = f"{amino_acid}{int(self.break_index) - 1}{self.break_id}{amino_acid}{after_break_size}_{match.span()[0]}to{match.span()[1]}"
        else:
            self.match_break = (
                f"{amino_acid}{self.length}_{match.span()[0]}to{match.span()[1]}"
            )

    def get_non_q_index(self, amino_acid):
        """Returns index and character of a non-Q match if found"""
        non_qmatch = re.search(f"[^{amino_acid}]", self.sequence)
        if non_qmatch:
            return non_qmatch.group(), str(non_qmatch.start() + 1)
        return None, None


class Fasta:
    @staticmethod
    def parse_generator(fasta_input_path):
        """Simple fasta file reader"""
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
    """Handles the matching of polys and sorting them into different outputs."""

    def __init__(self, input_dir, output_dir, input_basename, amino_acid):

        self.amino_acid = amino_acid
        self.fasta = Fasta()
        self.protein_dir = os.path.join(args.output_directory, "translate_out")
        self.output_dir = output_dir
        self.protein_file_path = os.path.join(self.protein_dir, input_basename)
        self.input_dir = input_dir
        self.nucleotide_file_path = os.path.join(input_dir, input_basename)

        ensure_directory_exists(os.path.join(output_dir, "protein_matches"))
        self.output_file_path = os.path.join(
            output_dir, "protein_matches", f"{os.path.splitext(input_basename)[0]}"
        )

        ensure_directory_exists(os.path.join(output_dir, "genome"))
        self.output_genome_file_path = os.path.join(
            output_dir, "genome", f"{os.path.splitext(input_basename)[0]}"
        )

        ensure_directory_exists(os.path.join(output_dir, "nucleotide_matches"))
        self.output_nucleotide_file_path = os.path.join(
            output_dir, "nucleotide_matches", f"{os.path.splitext(input_basename)[0]}"
        )

    def find_matches(self, pattern, header, sequence):
        matches = pattern.finditer(sequence)
        return [Match(match, self.amino_acid, header, sequence) for match in matches]

    @staticmethod
    def append_to_output(output_file, match, breaks, sequence):
        """Appends fasta match (header and poly info) information to the output file."""
        output_file.write(
            f"{match.fasta_id.strip()}_[poly={'_'.join(breaks)}]\n{sequence}\n"
        )

    def process_lines(self):
        """Processes lines in the data file, finds matches, and writes to report and output files."""
        protein_generator = self.fasta.parse_generator(self.protein_file_path)
        nucleotide_generator = self.fasta.parse_generator(self.nucleotide_file_path)
        for (prot_id, prot_sequence), (nuc_id, nuc_sequence) in zip(
            protein_generator, nucleotide_generator
        ):
            matches = self.find_matches(PATTERN, prot_id, prot_sequence)
            appended = False
            match_breaks = []
            if matches:
                if matches[0].fasta_seq not in seen_sequences:
                    for match in matches:
                        match_breaks.append(match.match_break)
                        if not appended:
                            seen_sequences.add(match.fasta_seq)
                            appended = True
                    # Appends only once for each sequence
                    self.append_to_output(
                        self.output_file, match, match_breaks, match.fasta_seq
                    )
                    self.append_to_output(
                        self.output_genome_file, match, match_breaks, nuc_sequence
                    )
                    self.append_to_output(
                        self.output_nucleotide_file, match, match_breaks, nuc_sequence
                    )
            else:
                self.output_genome_file.write(f"{prot_id.strip()}\n{nuc_sequence}\n")

    def process_file(self):
        with open(self.protein_file_path, "r") as data_file, open(
            self.output_file_path, "w"
        ) as self.output_file, open(
            self.output_genome_file_path, "w"
        ) as self.output_genome_file, open(
            self.output_nucleotide_file_path, "w"
        ) as self.output_nucleotide_file:

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
        help="The amino acid of chosen poly chain",
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
    )
    args = parser.parse_args()

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

    for input_basename in input_filenames:
        print(f"File: {input_basename}")
        poly = Poly(
            args.input_directory,
            args.output_directory,
            input_basename,
            args.poly_amino_acid,
        )
        seen_sequences = set()  # Reset for each file
        poly.process_file()
