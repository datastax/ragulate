import sys

from typing_extensions import Generic, Protocol

sys.modules["pip._vendor.typing_extensions"] = sys.modules["typing_extensions"]

from typing import Any, Dict, List, Tuple

import streamlit as st

from ragulate.data import get_all_recipes, get_datasets_and_metadata
from ragulate.ui.utils import write_button_row
from ragulate.ui import state

MetadataMap = Dict[str, Dict[str, Dict[str, Any]]]
DatasetToRecipeMap = Dict[str, List[str]]

DATASET_NONE = "<none>"

@st.cache_data
def get_datasets_and_recipes(
    timestamp: float,
) -> Tuple[DatasetToRecipeMap, MetadataMap]:
    dataset_to_recipe_map: DatasetToRecipeMap = {DATASET_NONE: []}
    metadata_map: MetadataMap = {}

    for recipe in get_all_recipes():
        for dataset, metadata in get_datasets_and_metadata(recipe=recipe).items():
            if dataset not in dataset_to_recipe_map:
                dataset_to_recipe_map[dataset] = []
                metadata_map[dataset] = {}
            dataset_to_recipe_map[dataset].append(recipe)
            metadata_map[dataset][recipe] = metadata

    return dataset_to_recipe_map, metadata_map

def dataset_key() -> str:
    return f"home_dataset"

def recipe_key(recipe: str, dataset:str) -> str:
    return f"checkbox_{recipe}_{dataset}"


def draw_page() -> None:
    st.set_page_config(page_title="Ragulate - Home", layout="wide")
    selected_dataset = state.get_selected_dataset()
    state.set_page_item_if_empty(key=dataset_key(), value=selected_dataset)

    button_row_container = st.container()

    st.write("Select Dataset and at least 2 Recipes to Compare...")

    dataset_to_recipe_map, metadata_map = get_datasets_and_recipes(
        timestamp=state.get_data_timestamp()
    )

    col1, col2 = st.columns(2)

    with col1:
        options = dataset_to_recipe_map.keys()

        dataset = st.radio(label="Dataset:", options=options, key=dataset_key())
        if dataset is not None and dataset != selected_dataset:
            if dataset == DATASET_NONE:
                state.set_selected_dataset(dataset=None)
                selected_dataset = None
            else:
                state.set_selected_dataset(dataset=dataset)
                selected_dataset = dataset

    with col2:
        st.write("Recipes:")
        if selected_dataset is not None:
            for selected_recipe in state.get_selected_recipes(dataset=selected_dataset):
                state.set_page_item_if_empty(recipe_key(selected_recipe, dataset=selected_dataset), True)

            for recipe in dataset_to_recipe_map[selected_dataset]:
                value = st.checkbox(label=recipe, key=recipe_key(recipe=recipe, dataset=selected_dataset))
                metadata = metadata_map[selected_dataset][recipe]
                del metadata["recipe_name"]
                del metadata["dataset_name"]
                with st.expander("metadata:", expanded=False):
                    st.json(metadata)
                state.set_recipe_state(recipe=recipe, value=value, dataset=selected_dataset)

    with button_row_container:
        selected_recipes = state.get_selected_recipes(dataset=selected_dataset)
        write_button_row("home", disable_non_home=len(selected_recipes) < 2)


draw_page()
