import asyncio
import sys
from typing import Any, Dict, List, Set, Tuple

from pandas import DataFrame

sys.modules["pip._vendor.typing_extensions"] = sys.modules["typing_extensions"]

# https://github.com/jerryjliu/llama_index/issues/7244:
asyncio.set_event_loop(asyncio.new_event_loop())

import streamlit as st
from plotly.io import to_html, to_image
from ragulate.analysis import Analysis
from ragulate.ui import state
from ragulate.ui.data import get_chart_data
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(page_title="Ragulate - Chart", layout="wide")


@st.cache_data
def get_data(
    recipes: List[str], dataset: str, metadata_filter: Dict[str, Any], timestamp: int
) -> Tuple[DataFrame, List[str]]:
    return get_chart_data(
        recipes=recipes, dataset=dataset, metadata_filter=metadata_filter
    )


metadata_filter = state.get_metadata_filter()
st.write(metadata_filter)

if st.button("home"):
    switch_page("home")

recipes = list(state.get_selected_recipes())
dataset = state.get_selected_dataset()


if dataset is None:
    switch_page("home")
else:
    df, feedbacks = get_data(
        recipes=recipes, dataset=dataset, metadata_filter=metadata_filter, timestamp=0
    )

    analysis = Analysis()

    figures = analysis.box_plots_by_dataset(df=df, metrics=feedbacks)

    if dataset not in figures:
        st.write("Analysis failed")
    else:
        svg_bytes = to_image(fig=figures[dataset], format="svg", scale=1.1)

        st.image(image=svg_bytes.decode("utf-8"))
        # st.html(to_html(fig=figures[dataset], full_html=False))

    col1, _, col3 = st.columns(3)

    if col1.button(label="Compare"):
        switch_page("compare")

    if col3.button(label="Filter"):
        switch_page("filter")
