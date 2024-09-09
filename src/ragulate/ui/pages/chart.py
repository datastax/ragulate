import io
import sys
from typing import Any, Dict, List, Tuple

from pandas import DataFrame

sys.modules["pip._vendor.typing_extensions"] = sys.modules["typing_extensions"]

import streamlit as st
from plotly.io import to_html, to_image
from ragulate.analysis import Analysis
from ragulate.data import get_chart_data
from ragulate.ui import state
from ragulate.ui.utils import write_button_row
from streamlit_extras.switch_page_button import switch_page


@st.cache_data
def get_data(
    recipes: List[str], dataset: str, metadata_filter: Dict[str, Any], timestamp: float
) -> Tuple[DataFrame, List[str]]:
    return get_chart_data(
        recipes=recipes, dataset=dataset, metadata_filter=metadata_filter
    )


def draw_page() -> None:
    st.set_page_config(page_title="Ragulate - Chart", layout="wide")
    button_row_container = st.container()

    dataset = state.get_selected_dataset()
    recipes = list(state.get_selected_recipes(dataset=dataset))
    if dataset is None or len(recipes) < 2:
        switch_page("home")
        return

    metadata_filter = state.get_metadata_filter(dataset=dataset)
    st.caption("metadata filter:")
    st.json(metadata_filter)

    df, feedbacks = get_data(
        recipes=recipes,
        dataset=dataset,
        metadata_filter=metadata_filter,
        timestamp=state.get_data_timestamp(),
    )

    analysis = Analysis()

    box_plots = analysis.box_plots_by_dataset(df=df, feedbacks=feedbacks)
    histograms = analysis.histograms_by_dataset(df=df, feedbacks=feedbacks)

    if dataset not in box_plots and dataset not in histograms:
        st.write("Analysis failed")
    else:
        svg_bytes = to_image(fig=box_plots[dataset], format="svg", scale=1.1)

        st.image(image=svg_bytes.decode("utf-8"))

        g = histograms[dataset]
        buffer = io.BytesIO()
        g.savefig(buffer)
        buffer.seek(0)
        st.image(buffer.read())

    with button_row_container:
        write_button_row(current_page="chart")


draw_page()
