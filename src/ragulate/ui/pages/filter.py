import sys
from typing import Any, Dict, List, Set

sys.modules["pip._vendor.typing_extensions"] = sys.modules["typing_extensions"]

import streamlit as st
from ragulate.data import get_metadata_options
from ragulate.ui import state
from ragulate.ui.utils import write_button_row
from streamlit_extras.switch_page_button import switch_page

SELECT_ALL_TEXT = "<all>"


@st.cache_data
def get_metadata_filter_options(
    recipes: List[str], dataset: str, timestamp: float
) -> Dict[str, Set[Any]]:
    return get_metadata_options(recipes=recipes, dataset=dataset)


def draw_page() -> None:
    st.set_page_config(page_title="Ragulate - Filter", layout="wide")
    button_row_container = st.container()

    recipes = list(state.get_selected_recipes())
    dataset = state.get_selected_dataset()
    if dataset is None or len(recipes) < 2:
        switch_page("home")
        return

    metadata_filter = state.get_metadata_filter()
    for key, value in metadata_filter.items():
        state.set_page_item_if_empty(key=f"select_filter_{key}", value=value)

    metadata_options = get_metadata_filter_options(
        recipes=recipes, dataset=dataset, timestamp=state.get_data_timestamp()
    )

    def set_metadata_filter() -> None:
        filter: Dict[str, Any] = {}
        for key in metadata_options.keys():
            value = state.get_page_item(key=f"select_filter_{key}")
            if value != SELECT_ALL_TEXT:
                filter[key] = value
        state.set_metadata_filter(filter=filter)

    for key, options in metadata_options.items():
        sorted_options = sorted(list(options))
        sorted_options.insert(0, SELECT_ALL_TEXT)
        st.selectbox(
            label=key,
            options=sorted_options,
            key=f"select_filter_{key}",
            on_change=set_metadata_filter,
        )

    with button_row_container:
        write_button_row(current_page="filter")


draw_page()
