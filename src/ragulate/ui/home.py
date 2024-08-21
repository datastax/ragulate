import asyncio
import glob
import os
import sys

from typing_extensions import Generic, Protocol

sys.modules["pip._vendor.typing_extensions"] = sys.modules["typing_extensions"]

# https://github.com/jerryjliu/llama_index/issues/7244:
asyncio.set_event_loop(asyncio.new_event_loop())

from typing import Dict, List

import state
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from ragulate.utils import get_tru

if __name__ == "__main__":
    if "home_cache_time" not in st.session_state:
        st.session_state.home_cache_time = 0

    # restore dataset selector state
    if state.dataset_key() not in st.session_state:
        state.set_page_item(state.dataset_key(), state.get_selected_dataset())

        # restore recipe selector state
        for selected_recipe in state.get_selected_recipes():
            state.set_page_item(state.recipe_key(selected_recipe), True)


@st.cache_data
def get_datasets_and_recipes(timestamp: int) -> Dict[str, List[str]]:
    dataset_to_recipe_map: Dict[str, List[str]] = {"<none>": []}

    for file in glob.glob(os.path.join("*.sqlite")):
        recipe_name = file.removesuffix(".sqlite")
        tru = get_tru(recipe_name=recipe_name)

        for app in tru.get_apps():
            dataset = app["app_id"]
            if dataset not in dataset_to_recipe_map:
                dataset_to_recipe_map[dataset] = []
            dataset_to_recipe_map[dataset].append(recipe_name)

        tru.delete_singleton()

    return dataset_to_recipe_map


def home() -> None:
    """Render the home page."""

    st.write("Select Dataset and at least 2 Recipes to Compare...")

    dataset_to_recipe_map = get_datasets_and_recipes(st.session_state.home_cache_time)

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
                state.set_recipe_state(recipe=recipe, value=value)

    selected_recipes = state.get_selected_recipes()

    if st.button("Compare", key="button_compare", disabled=len(selected_recipes) < 2):
        switch_page("compare")


if __name__ == "__main__":
    home()
