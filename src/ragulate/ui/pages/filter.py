import asyncio
import sys
from typing import Any, Dict, List, Set

sys.modules["pip._vendor.typing_extensions"] = sys.modules["typing_extensions"]

# https://github.com/jerryjliu/llama_index/issues/7244:
asyncio.set_event_loop(asyncio.new_event_loop())

import streamlit as st
from ragulate.ui import state
from ragulate.ui.data import get_metadata_options
from streamlit_extras.switch_page_button import switch_page

SELECT_ALL_TEXT = "<all>"

st.set_page_config(page_title="Ragulate - Filter", layout="wide")

metadata_filter = state.get_metadata_filter()
for key, value in metadata_filter.items():
    state.set_page_item_if_empty(key=f"select_filter_{key}", value=value)


@st.cache_data
def get_metadata_filter_options(
    recipes: List[str], dataset: str, timestamp: int
) -> Dict[str, Set[Any]]:
    return get_metadata_options(recipes=recipes, dataset=dataset)


if st.button("home"):
    state.clear_page_loaded("filter")
    switch_page("home")

recipes = list(state.get_selected_recipes())
dataset = state.get_selected_dataset()

if dataset is None:
    switch_page("home")
else:
    metadata_options = get_metadata_filter_options(
        recipes=recipes, dataset=dataset, timestamp=0
    )

    for key, options in metadata_options.items():
        sorted_options = sorted(list(options))
        sorted_options.insert(0, SELECT_ALL_TEXT)
        st.selectbox(label=key, options=sorted_options, key=f"select_filter_{key}")

    def set_metadata_filter() -> None:
        filter: Dict[str, Any] = {}
        for key in metadata_options.keys():
            value = state.get_page_item(key=f"select_filter_{key}")
            if value != SELECT_ALL_TEXT:
                filter[key] = value
        state.set_metadata_filter(filter=filter)

    col1, col2, _ = st.columns(3)

    if col1.button(label="Compare"):
        set_metadata_filter()
        switch_page("compare")

    if col2.button(label="Chart"):
        set_metadata_filter()
        switch_page("chart")
