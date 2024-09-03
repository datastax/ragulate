import sys
import time
from typing import Any, Dict, List, Set

import streamlit as st


def dataset_key() -> str:
    return f"home_dataset"


def recipe_key(recipe: str) -> str:
    return f"checkbox_{recipe}"


def get_selected_dataset() -> str | None:
    if "selected_dataset" not in st.session_state:
        st.session_state["selected_dataset"] = None
    selected_dataset: str | None = st.session_state["selected_dataset"]
    return selected_dataset


def set_selected_dataset(dataset: str) -> None:
    st.session_state["selected_dataset"] = dataset


def clear_selected_recipes() -> None:
    st.session_state["selected_recipes"] = set()


def get_metadata_filter() -> Dict[str, Any]:
    if "metadata_filter" not in st.session_state:
        st.session_state["metadata_filter"] = {}
    metadata_filter: Dict[str, Any] = st.session_state["metadata_filter"]
    return metadata_filter


def set_metadata_filter(filter: Dict[str, Any]) -> None:
    st.session_state["metadata_filter"] = filter


def get_selected_recipes() -> Set[str]:
    if "selected_recipes" not in st.session_state:
        clear_selected_recipes()
    selected_recipes: Set[str] = st.session_state["selected_recipes"]
    return selected_recipes


def get_recipe_state(recipe: str) -> bool:
    return recipe in get_selected_recipes()


def set_recipe_state(recipe: str, value: bool) -> None:
    if value:
        st.session_state["selected_recipes"].add(recipe)
    else:
        st.session_state["selected_recipes"].discard(recipe)


def set_page_item(key: str, value: Any) -> None:
    st.session_state[key] = value


def set_page_item_if_empty(key: str, value: Any) -> None:
    if key not in st.session_state:
        st.session_state[key] = value


def get_page_item(key: str) -> Any | None:
    if key in st.session_state:
        return st.session_state[key]
    return None


def set_page_loaded(page: str) -> None:
    st.session_state[f"page_{page}"] = True


def get_page_loaded(page: str) -> bool:
    return st.session_state.get(f"page_{page}", False)


def clear_page_loaded(page: str) -> None:
    if f"page_{page}" in st.session_state:
        del st.session_state[f"page_{page}"]


def set_data_timestamp() -> None:
    st.session_state["data_timestamp"] = time.time()


def get_data_timestamp() -> float:
    return st.session_state.get("data_timestamp", 0.0)
