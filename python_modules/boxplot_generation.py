import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
import sys
import argparse


class Boxplot:
    def __init__(
        self,
        datasets,
        titles=None,
        tick_labels=None,
        y_labels=None,
        figsize=None,
        locator=None,
        median_color="black",
        notch=False,
        grid=False,
    ):
        """
        Initialize the Boxplot with datasets, titles, tick labels, and y-axis labels.

        :param datasets: List of datasets for the boxplots. eg: [[data],]
        :param titles: List of titles for the graphs. eg: [title,]
        :param tick_labels: List of tick label list for the x-axis. eg: [[label,],]
        :param y_labels: List of y-axis labels for each graph.
        :param figsize: Figure size (width, height per row).
        :param locator: Division of y label locator (int divison, number of subdivisions).
        :param notch: Boolean to notch or not to notch, that is the question.
        :param grid: Boolean. Generate horizontal y grid lines.
        """
        self.datasets = [self._validate_dataset(data) for data in datasets]
        self.titles = titles or [f"Graph {i + 1}" for i in range(len(self.datasets))]
        self.tick_labels = tick_labels or [None] * len(self.datasets)
        self.y_labels = y_labels or [None] * len(self.datasets)
        self.figsize = figsize
        self.locator = locator
        self.median_color = median_color
        self.notch = notch
        self.grid = grid

        if len(self.titles) != len(self.datasets):
            sys.exit("Number of titles must match the number of datasets.")
        if len(self.tick_labels) != len(self.datasets):
            sys.exit("Number of tick label sets must match the number of datasets.")
        if len(self.y_labels) != len(self.datasets):
            sys.exit("Number of y-axis labels must match the number of datasets.")

    @staticmethod
    def _validate_dataset(dataset):
        """
        Validate and convert dataset to numeric format.
        """
        if isinstance(dataset[0], (int, float)):
            dataset = [dataset]  # Wrap single list in a list
        return [np.array(d, dtype=float) for d in dataset]

    def _plot_single_graph(self, ax, data, title, tick_labels, y_label):
        """
        Plot a single graph with multiple boxplots, ensuring long labels don't overlap.
        """

        if len(tick_labels) != len(data):
            sys.exit(
                f"Number of tick label sets must match the number boxplots of dataset {title}."
            )

        num_boxes = len(data)
        widths = max(0.3, min(0.3, 1.0 / num_boxes))

        boxplot_elements = ax.boxplot(data, widths=widths, notch=self.notch)
        ax.set_title(title, pad=15)

        # x-axis tick labels
        if tick_labels:
            ax.set_xticks(range(1, len(tick_labels) + 1))
            ax.set_xticklabels(tick_labels, rotation=45, ha="right")  # Rotate labels
        else:
            ax.set_xticks(range(1, num_boxes + 1))
            ax.set_xticklabels(
                [f"Box {i + 1}" for i in range(num_boxes)], rotation=45, ha="right"
            )

        # y-axis label
        if y_label:
            ax.set_ylabel(y_label)

        # padding for labels
        ax.tick_params(axis="x", pad=10)

        # customize median color
        for median in boxplot_elements["medians"]:
            median.set_color(self.median_color)

        ax.grid(axis="y", color="gray", linestyle="--", linewidth=0.5, alpha=0.4)

        if self.locator:
            # major and minor ticks
            y_min, y_max = ax.get_ylim()
            ax.yaxis.set_major_locator(MultipleLocator(self.locator[0]))  # Major ticks
            ax.yaxis.set_minor_locator(AutoMinorLocator(self.locator[1]))  # Minor ticks

            # appearance of minor ticks
            ax.tick_params(axis="y", which="minor", length=4, color="gray")

    def plot(self, save_path_prefix=None):
        """
        Create and save/display individual boxplots as separate SVG files.

        :param save_path_prefix: If provided, saves each plot to a separate SVG file
                                with this prefix followed by an index.
                                If not provided, displays the plots one by one.
        """

        if save_path_prefix:
            plt.style.use("default")

        num_plots = len(self.datasets)

        if num_plots == 0:
            sys.exit("No datasets provided for boxplots.")

        file_name_counts = {}  # Dictionary to track counts for each base file name

        for data, title, tick_labels, y_label in zip(
            self.datasets, self.titles, self.tick_labels, self.y_labels
        ):
            # Determine figure size
            if self.figsize:
                figsize = self.figsize
            else:
                # Dynamic sizing: width based on number of boxes, height fixed
                num_boxes = len(data)
                if num_boxes < 10:
                    width = max(4, num_boxes + 0.65 * num_boxes)
                elif num_boxes < 20:
                    width = num_boxes
                else:
                    width = num_boxes / 2

                height = 6  # Fixed height
                figsize = (width, height)

            fig, ax = plt.subplots(figsize=figsize)  # New figure for each plot

            # Plot the data
            self._plot_single_graph(ax, data, title, tick_labels, y_label)

            fig.tight_layout()

            if save_path_prefix:
                base_file_name = (
                    f"{title.replace(' ', '_').replace('/', '')}_plot".lower()
                )

                # Start the counter at 0
                if base_file_name not in file_name_counts:
                    file_name_counts[base_file_name] = 0
                else:
                    file_name_counts[base_file_name] += 1

                # Append counter only if it's 1 or higher
                if file_name_counts[base_file_name] > 0:
                    file_path = f"{save_path_prefix}{base_file_name}_{file_name_counts[base_file_name]}.svg"
                else:
                    file_path = f"{save_path_prefix}{base_file_name}.svg"

                # Save the file
                plt.savefig(file_path, bbox_inches="tight", format="svg")
                print(f"Plot '{title}' saved to {file_path}.")
            else:
                plt.show()

            plt.close(fig)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Graph generator by family for poly module."
    )
    parser.add_argument(
        "-d",
        "--data",
        help="List of lists containing numeric data, or even lists given multiple boxplots in one graph",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--titles",
        help="List of titles, one required per data list",
        required=True,
    )
    parser.add_argument(
        "-l",
        "--labels",
        help="List containing one list per dataset, with the number of entries being equal to the number of graph entries",
        required=True,
    )
    parser.add_argument(
        "-yl",
        "--yaxislabels",
        help="List of y_label names for each graph, one required per graph",
        required=True,
    )
    parser.add_argument(
        "-od",
        "--output_directory",
        help="Output directory for csv to be saved",
        required=True,
    )
    parser.add_argument(
        "-n",
        "--notched",
        help="Set to true if notch in boxplot is desired",
        default=False,
    )
    parser.add_argument(
        "-fs",
        "--fig_size",
        help="Pass a set (y,x) size.",
    )

    args = parser.parse_args()

    boxplot_dynamic = Boxplot(
        datasets=args.data,
        titles=args.titles,
        tick_labels=args.labels,
        y_labels=args.yaxislabels,
        notch=args.notched,
        figsize=args.fig_size,
    )

    boxplot_dynamic.plot(args.output_directory)

# example usage

# big_list = []
# for i in range(30):
#     for i in range(30):
#         big_list.append(i)

# data = [
#     [1, 2, 3, 4, 5, 6, 7, 8, 9],
#     [
#         big_list,
#         big_list[22:45],
#         big_list[3:15],
#         big_list[8:23],
#         big_list[55:89],
#     ],
# ]

# titles = ["Single Plot", "Multiple Plot"]

# labels = [
#     ["Numbers"],
#     [
#         "Drosophila melanogaster",
#         "Homo sapiens",
#         "Raphus cucullatus",
#         "Bradypus variegatus",
#         "Ankylosaurus magniventris",
#     ],
# ]

# y_labels = ["Value", "Measurement"]

# # with dynamic sizing
# boxplot_dynamic = Boxplot(
#     datasets=data,
#     titles=titles,
#     tick_labels=labels,
#     y_labels=y_labels,
#     locator=(5, 2),
#     notch=True,
# )
# boxplot_dynamic.plot("./results/dynamic")

# # with fixed figsize
# boxplot_fixed = Boxplot(
#     datasets=data, titles=titles, tick_labels=labels, y_labels=y_labels, figsize=(8, 6)
# )
# boxplot_fixed.plot("./results/fixed")
