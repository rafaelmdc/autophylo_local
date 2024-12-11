import sys
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


def translate_fasta_no_header_change(input_path, output_path):
    translated_records = []

    for record in SeqIO.parse(input_path, "fasta"):
        # Trim the sequence length to the nearest length divisible by 3
        trimmed_seq = record.seq[: len(record.seq) - (len(record.seq) % 3)]
        # Translate the trimmed nucleic acid sequence to a protein sequence
        protein_seq = trimmed_seq.translate(to_stop=True)
        # Remove stop codons ('*') from the protein sequence
        cleaned_protein_seq = Seq(str(protein_seq).replace("*", ""))
        # Create a new SeqRecord, preserving the original header
        translated_record = SeqRecord(
            cleaned_protein_seq, id=record.id, description=record.description
        )
        translated_records.append(translated_record)

    # Write the translated protein sequences to the output file
    with open(output_path, "w") as output_file:
        SeqIO.write(translated_records, output_file, "fasta")


def main():
    if len(sys.argv) != 3:
        print(
            "Usage: python translate_fasta_no_header_change.py <input_fasta_path> <output_fasta_path>"
        )
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    translate_fasta_no_header_change(input_path, output_path)

if __name__ == "__main__":
    main()
