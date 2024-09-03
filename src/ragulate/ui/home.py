import asyncio
import sys

from typing_extensions import Generic, Protocol

sys.modules["pip._vendor.typing_extensions"] = sys.modules["typing_extensions"]

# https://github.com/jerryjliu/llama_index/issues/7244:
asyncio.set_event_loop(asyncio.new_event_loop())

from typing import Any, Dict, List, Tuple

import state
import streamlit as st

from ragulate.data import get_all_recipes, get_datasets_and_metadata
from ragulate.ui.utils import write_button_row

if __name__ == "__main__":
    if "home_cache_time" not in st.session_state:
        st.session_state.home_cache_time = 0

    # restore dataset selector state
    if state.dataset_key() not in st.session_state:
        state.set_page_item(state.dataset_key(), state.get_selected_dataset())

        # restore recipe selector state
        for selected_recipe in state.get_selected_recipes():
            state.set_page_item(state.recipe_key(selected_recipe), True)

MetadataMap = Dict[str, Dict[str, Dict[str, Any]]]
DatasetToRecipeMap = Dict[str, List[str]]


@st.cache_data
def get_datasets_and_recipes(timestamp: int) -> Tuple[DatasetToRecipeMap, MetadataMap]:
    dataset_to_recipe_map: DatasetToRecipeMap = {"<none>": []}
    metadata_map: MetadataMap = {}

    for recipe in get_all_recipes():
        for dataset, metadata in get_datasets_and_metadata(recipe=recipe).items():
            if dataset not in dataset_to_recipe_map:
                dataset_to_recipe_map[dataset] = []
                metadata_map[dataset] = {}
            dataset_to_recipe_map[dataset].append(recipe)
            metadata_map[dataset][recipe] = metadata

    return dataset_to_recipe_map, metadata_map


def draw_page() -> None:
    st.set_page_config(page_title="Ragulate - Home", layout="wide")
    button_row_container = st.container()

    st.write("Select Dataset and at least 2 Recipes to Compare...")

    dataset_to_recipe_map, metadata_map = get_datasets_and_recipes(
        st.session_state.home_cache_time
    )

    col1, col2 = st.columns(2)

    with col1:
        selected_dataset = state.get_selected_dataset()
        options = dataset_to_recipe_map.keys()

        dataset = st.radio(label="Dataset:", options=options, key=state.dataset_key())
        if dataset is not None and dataset != selected_dataset:
            state.set_selected_dataset(dataset=dataset)
            state.clear_selected_recipes()
            selected_dataset = dataset

    with col2:
        st.write("Recipes:")
        if selected_dataset is not None:
            for recipe in dataset_to_recipe_map[selected_dataset]:
                value = st.checkbox(label=recipe, key=state.recipe_key(recipe=recipe))
                metadata = metadata_map[selected_dataset][recipe]
                del metadata["recipe_name"]
                del metadata["dataset_name"]
                with st.expander("metadata:", expanded=False):
                    st.json(metadata)
                state.set_recipe_state(recipe=recipe, value=value)

    with button_row_container:
        selected_recipes = state.get_selected_recipes()
        write_button_row("home", disable_non_home=len(selected_recipes) < 2)


draw_page()
