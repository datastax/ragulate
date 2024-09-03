from __future__ import annotations

from typing import Any, Dict, Set

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import seaborn as sns
from plotly.io import write_image

from ragulate.data import get_chart_data, get_datasets_and_metadata


class Analysis:
    """Analysis class."""

    def calculate_statistics(
        self, df: pd.DataFrame, feedbacks: list[str]
    ) -> dict[str, Any]:
        """Calculate statistics."""
        stats: dict[str, Any] = {}
        for recipe in df["recipe"].unique():
            stats[recipe] = {}
            for feedback in feedbacks:
                stats[recipe][feedback] = {}
                for dataset in df["dataset"].unique():
                    data = df[(df["recipe"] == recipe) & (df["dataset"] == dataset)][
                        feedback
                    ]
                    stats[recipe][feedback][dataset] = {
                        "high": data.max(),
                        "low": data.min(),
                        "median": data.median(),
                        "mean": data.mean(),
                        "1st_quartile": data.quantile(0.25),
                        "3rd_quartile": data.quantile(0.75),
                    }
        return stats

    def box_plots_by_dataset(
        self, df: pd.DataFrame, feedbacks: list[str]
    ) -> Dict[str, go.Figure]:
        """Output box plots by dataset."""
        stats = self.calculate_statistics(df, feedbacks)
        recipes = sorted(df["recipe"].unique(), key=lambda x: x.lower())
        datasets = sorted(df["dataset"].unique(), key=lambda x: x.lower())
        feedbacks = sorted(feedbacks)
        feedbacks.reverse()

        longest_feedback = 0
        for feedback in feedbacks:
            longest_feedback = max(longest_feedback, len(feedback))

        # generate an array of rainbow colors by fixing the saturation and lightness of
        # the HSL representation of color and marching around the hue.
        c = [
            "hsl(" + str(h) + ",50%" + ",50%)"
            for h in np.linspace(0, 360, len(recipes) + 1)
        ]

        height = max((len(feedbacks) * len(recipes) * 20) + 150, 450)

        figures: Dict[str, go.Figure] = {}

        for dataset in datasets:
            fig = go.Figure()
            for test_index, recipe in enumerate(recipes):
                y = []
                x = []
                q1 = []
                median = []
                q3 = []
                low = []
                high = []
                for feedback in feedbacks:
                    stat = stats[recipe][feedback][dataset]
                    y.append(feedback)
                    x.append(stat["mean"])
                    q1.append(stat["1st_quartile"])
                    median.append(stat["median"])
                    q3.append(stat["3rd_quartile"])
                    low.append(stat["low"])
                    high.append(stat["high"])

                fig.add_trace(
                    go.Box(
                        y=y,
                        q1=q1,
                        median=median,
                        q3=q3,
                        mean=[],
                        lowerfence=low,
                        upperfence=high,
                        name=recipe,
                        marker_color=c[test_index],
                        visible=True,
                        boxpoints=False,  # Do not show individual points
                    )
                )

            fig.update_traces(
                orientation="h",
                boxmean=True,
                jitter=1,
            )
            fig.update_layout(
                margin_l = longest_feedback * 7,
                boxmode="group",
                height=height,
                width=900,
                title={
                    "text": dataset,
                    "x": 0.03,
                    "y": 0.03,
                    "xanchor": "left",
                    "yanchor": "bottom",
                },
                yaxis_title="metric",
                xaxis_title="score",
                legend={
                    "orientation": "h",
                    "yanchor": "bottom",
                    "y": 1.02,
                    "xanchor": "right",
                    "x": 1,
                },
            )
            figures[dataset] = fig
        return figures

    def output_box_plots_by_dataset(
        self, df: pd.DataFrame, feedbacks: list[str]
    ) -> None:
        figures = self.box_plots_by_dataset(df=df, feedbacks=feedbacks)

        for dataset, fig in figures.items():
            write_image(fig, f"./{dataset}_box_plot.png")

    def histograms_by_dataset(
        self, df: pd.DataFrame, feedbacks: list[str]
    ) -> Dict[str, sns.FacetGrid]:
        """Output histograms by dataset."""
        # Append "latency" to the feedbacks list
        feedbacks.append("latency")

        # Get unique datasets
        datasets = df["dataset"].unique()

        figures: Dict[str, sns.FacetGrid] = {}

        for dataset in datasets:
            # Filter DataFrame for the current dataset
            df_filtered = df[df["dataset"] == dataset]

            # Melt the DataFrame to long format
            df_melted = pd.melt(
                df_filtered,
                id_vars=["record_id", "recipe", "dataset"],
                value_vars=feedbacks,
                var_name="metric",
                value_name="value",
            )

            # Set the theme for the plot
            sns.set_theme(style="darkgrid")

            # Custom function to set bin ranges and filter invalid values
            def custom_hist(data: dict[str, Any], **kws: Any) -> None:
                feedback = data["metric"].iloc[0]
                data = data[
                    np.isfinite(data["value"])
                ]  # Remove NaN and infinite values
                data = data[data["value"] >= 0]  # Ensure no negative values
                if feedback == "latency":
                    bins = np.concatenate(
                        [
                            np.linspace(
                                0,
                                15,
                            ),
                            [np.inf],
                        ]
                    )  # 46 bins from 0 to 15 seconds, plus one for >15 seconds
                    sns.histplot(data, x="value", bins=bins, stat="percent", **kws)
                else:
                    bin_range = (0, 1)
                    sns.histplot(
                        data,
                        x="value",
                        stat="percent",
                        bins=10,
                        binrange=bin_range,
                        **kws,
                    )

            # Create the FacetGrid
            g = sns.FacetGrid(
                df_melted,
                col="metric",
                row="recipe",
                margin_titles=True,
                height=3.5,
                aspect=1,
                sharex="col",
                legend_out=False,
            )

            g.set_titles(row_template="{row_name}", col_template="{col_name}")

            # Map the custom histogram function to the FacetGrid
            g.map_dataframe(custom_hist)

            for ax, feedback in zip(
                g.axes.flat, g.col_names * len(g.row_names), strict=False
            ):
                ax.set_ylim(0, 100)
                # Set custom x-axis label
                if feedback == "latency":
                    ax.set_xlabel("Seconds")
                else:
                    ax.set_xlabel("Score")

            g.set_axis_labels(y_var="Percentage")

            # Set the title for the entire figure
            g.figure.suptitle(dataset, fontsize=16)

            # Adjust the layout to make room for the title
            g.figure.subplots_adjust(top=0.9)

            figures[dataset] = g

        return figures

    def output_histograms_by_dataset(
        self, df: pd.DataFrame, feedbacks: list[str]
    ) -> None:
        figures = self.histograms_by_dataset(df=df, feedbacks=feedbacks)
        for dataset, g in figures.items():
            # Save the plot as a PNG file
            g.savefig(f"./{dataset}_histogram_grid.png")

            # Close the plot to avoid displaying it
            plt.close()

    def compare(self, recipes: list[str], output: str = "box-plots") -> None:
        """Compare results from 2 (or more) recipes."""
        unique_datasets: Set[str] = set()
        for recipe in recipes:
            datasets = get_datasets_and_metadata(recipe=recipe).keys()
            unique_datasets = unique_datasets.union(datasets)

        for dataset in unique_datasets:
            df, feedbacks = get_chart_data(
                recipes=recipes, dataset=dataset, metadata_filter={}
            )
            if output == "box-plots":
                self.output_box_plots_by_dataset(df=df, feedbacks=feedbacks)
            elif output == "histogram-grid":
                self.output_histograms_by_dataset(df=df, feedbacks=feedbacks)
            else:
                raise ValueError(f"Invalid output type: {output}")
