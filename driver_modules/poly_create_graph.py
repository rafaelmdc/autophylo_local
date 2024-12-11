import argparse
import os
import re
import shutil
import pandas as pd
import re
import math
from boxplotGeneration import Boxplot


class csvFixer:

    def __init__(self, out_dir, input_dir, report_dir):
        self.out_dir = out_dir
        self.input_dir = input_dir
        self.report_dir = report_dir

    def create_taxonomy_dir(self):
        for file in os.listdir(self.report_dir):
            file_path = os.path.join(self.report_dir, file)
            if not os.path.isfile(file_path):
                continue  # Skip directories or non-file items

            # Extract taxonomy name from the file name
            tax_name_match = re.search(r".*_([^_]+ae)_.*", file)
            if not tax_name_match:
                exit(f"No taxon found for {tax_name_match}")

            tax_name = tax_name_match.group(1)
            tax_dir = os.path.join(self.report_dir, tax_name)

            # Create directory if it doesn't exist
            os.makedirs(tax_dir, exist_ok=True)

            # Move file to the taxonomy-specific directory
            destination_path = os.path.join(tax_dir, file)
            shutil.move(file_path, destination_path)


class DataRetrieve:

    def __init__(self, file_path):
        self.data = pd.read_csv(file_path)

    def get_column_list(self, column_name):
        res = [i for i in self.data[column_name]]
        return res

    def get_start_indexes(
        self,
    ):
        match_start = self.get_column_list("Match Start")
        match_start = [(x) * 3 for x in match_start]
        total_length = []

        for index, row in self.data.iterrows():
            total_length.append(len(row["rootseq"]) * 3)

        start_point = [
            round((x / y) * 100, 2) for x, y in zip(match_start, total_length)
        ]

        return start_point

    def name_repeats(self):
        """Returns isoform repeats from csv as a list."""
        repeats_list = []  # Initialize an empty list
        old_name = ""
        repeat = 1

        for _, row in self.data.iterrows():
            new_name = row["Seq Name"]

            if old_name and new_name != old_name:
                repeats_list.append(repeat)  # Append the repeat count to the list
                repeat = 1  # Reset the repeat count
            elif old_name and new_name == old_name:
                repeat += 1

            old_name = new_name

        # Add the final repeat count for the last group
        repeats_list.append(repeat)

        return repeats_list

    def name_repeats_dict(self):
        """Returns isoform count from CSV as dict."""
        name_repeats = {}
        old_name = ""
        repeat = 1

        for _, row in self.data.iterrows():
            new_name = row["Seq Name"]

            if old_name and new_name != old_name:
                if repeat in name_repeats:
                    name_repeats[repeat] += 1
                else:
                    name_repeats[repeat] = 1
                repeat = 1
            elif old_name and new_name == old_name:
                repeat += 1

            old_name = new_name

        # Add the final count for the last group
        if repeat in name_repeats:
            name_repeats[repeat] += 1
        else:
            name_repeats[repeat] = 1

        return name_repeats

    def get_column_list(self, column_name):
        res = [i for i in self.data[column_name]]
        return res

    def caacag_relations(self):
        nucleotide_data = self.get_column_list("nucseq")
        polyQ_nucleotide = []  # Initialize an empty list

        for nucleotide, match_index, length_value in zip(
            nucleotide_data,
            [x * 3 for x in self.get_column_list("Match Start")],
            self.get_column_list("Length"),
        ):
            polyQ_nucleotide.append(
                nucleotide[match_index : match_index + length_value * 3]
            )

        codons_count = []  # Initialize an empty list
        for sequence in polyQ_nucleotide:
            caa = 0
            cag = 0
            for i in range(0, len(sequence), 3):
                value = sequence[i : i + 3]
                if value.upper() == "CAG":
                    cag += 1
                elif value.upper() == "CAA":
                    caa += 1
            if caa != 0:
                relation = round(cag / caa, 3)
            else:
                relation = float(
                    cag
                )  # Ensure cag is treated as a float for consistency
            codons_count.append(relation)

        return codons_count


if __name__ == "__main__":

    print("Filtering by taxon")

    parser = argparse.ArgumentParser(
        description="Graph generator by family for poly module."
    )
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
        "-rd",
        "--report_directory",
        help="Directory containing the report files",
        required=True,
    )

    args = parser.parse_args()

    csv_fixer = csvFixer(
        args.output_directory, args.input_directory, args.report_directory
    )

    # TODO make each taxonomy go to their directory?
    csv_fixer.create_taxonomy_dir()

    full_data_list = [[], [], [], [], [], []]
    labels = [[], [], [], [], [], []]
    titles = []
    ylabels = []

    for taxonomy in os.listdir(args.report_directory):
        file = os.listdir(os.path.join(args.report_directory, taxonomy))
        csv_path = os.path.join(args.report_directory, taxonomy, file[0])
        datamanager = DataRetrieve(file_path=csv_path)

        # data
        lenght_data = datamanager.get_column_list("Length")
        full_data_list[0].append(lenght_data)

        start_point = datamanager.get_start_indexes()
        full_data_list[1].append(lenght_data)

        name_repeats = datamanager.name_repeats()
        full_data_list[2].append(name_repeats)

        log_name_repeats = [math.log2(x) for x in name_repeats]
        full_data_list[3].append(log_name_repeats)

        polycodons = datamanager.caacag_relations()
        full_data_list[4].append(polycodons)

        log_polycodons = [round(math.log2(x), 3) for x in polycodons]
        full_data_list[5].append(log_polycodons)

        [labels[x].append(taxonomy) for x in range(6)]

    y_labels = [
        "Count",
        "Count",
        "Log2 count",
        "start point in %",
        "Count",
        "Log2 count",
    ]

    titles = [
        "Length of polyQ",
        "Appearences per protein",
        "Log appearences",
        "Starting point of polyQ",
        "CAG/CAA relation",
        "CAG/CAA relation log2",
    ]

    boxplot_dynamic = Boxplot(
        datasets=full_data_list,
        titles=titles,
        tick_labels=labels,
        y_labels=y_labels,
    )

    boxplot_dynamic.plot(args.output_directory)
