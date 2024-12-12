import argparse
import os
import re
import shutil
import pandas as pd
import re
import math
from boxplot_generation import Boxplot


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

    csv_fixer.create_taxonomy_dir()

    titles = []
    ylabels = []

    full_data_list = [[] for _ in range(6)]
    labels = [[] for _ in range(6)]

    for taxonomy in os.listdir(args.report_directory):
        # Get all files in the taxonomy directory
        files = os.listdir(os.path.join(args.report_directory, taxonomy))

        merged_length_data = []
        merged_start_point = []
        merged_name_repeats = []
        merged_log_name_repeats = []
        merged_polycodons = []
        merged_log_polycodons = []

        for file in files:
            csv_path = os.path.join(args.report_directory, taxonomy, file)
            datamanager = DataRetrieve(file_path=csv_path)

            merged_length_data.extend(datamanager.get_column_list("Length"))
            merged_start_point.extend(datamanager.get_start_indexes())

            name_repeats = datamanager.name_repeats()
            merged_name_repeats.extend(name_repeats)
            merged_log_name_repeats.extend([math.log2(x) for x in name_repeats])

            polycodons = datamanager.caacag_relations()
            merged_polycodons.extend(polycodons)
            merged_log_polycodons.extend(
                [round(math.log2(x), 8) if x != 0 else 0 for x in polycodons]
            )

        full_data_list[0].append(merged_length_data)
        full_data_list[1].append(merged_start_point)
        full_data_list[2].append(merged_name_repeats)
        full_data_list[3].append(merged_log_name_repeats)
        full_data_list[4].append(merged_polycodons)
        full_data_list[5].append(merged_log_polycodons)

        [labels[x].append(taxonomy) for x in range(6)]

    print(len(labels[1]))
    print(labels[1])

    y_labels = [
        "Count",
        "Start point in %",
        "Count",
        "Log 2 count",
        "CAG/CAA frequency",
        "Log2 Relation",
    ]

    titles = [
        "Length of polyQ",
        "Start point",
        "Poly count per protein",
        "Log2 Poly count per portein",
        "CAG/CAA relation",
        "Log2 CAG/CAA frequency",
    ]

    boxplot_dynamic = Boxplot(
        datasets=full_data_list,
        titles=titles,
        tick_labels=labels,
        y_labels=y_labels,
    )

    boxplot_dynamic.plot(args.output_directory)
