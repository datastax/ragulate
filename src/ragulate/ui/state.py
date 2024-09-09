import sys
import time
from typing import Any, Dict, List, Set

import streamlit as st

### Get/Set Selected Dataset

def get_selected_dataset() -> str | None:
    if "selected_dataset" not in st.session_state:
        st.session_state["selected_dataset"] = None
    selected_dataset: str | None = st.session_state["selected_dataset"]
    return selected_dataset

def set_selected_dataset(dataset: str| None) -> None:
    st.session_state["selected_dataset"] = dataset

### Get/Set Metadata Filter

def metadata_filter_key(dataset: str) -> str:
    return f"metadata_filter_{dataset}"

def get_metadata_filter(dataset: str) -> Dict[str, Any]:
    key = metadata_filter_key(dataset=dataset)
    if key not in st.session_state:
        st.session_state[key] = {}
    metadata_filter: Dict[str, Any] = st.session_state[key]
    return metadata_filter

def set_metadata_filter(filter: Dict[str, Any], dataset: str) -> None:
    st.session_state[metadata_filter_key(dataset=dataset)] = filter

### Get/Set Selected Recipes

def selected_recipes_key(dataset: str) -> str:
    return f"selected_recipes_{dataset}"

def get_selected_recipes(dataset: str) -> Set[str]:
    if dataset is None:
        return set()
    key = selected_recipes_key(dataset=dataset)
    if key not in st.session_state:
        st.session_state[key] = set()
    selected_recipes: Set[str] = st.session_state[key]
    return selected_recipes

def set_recipe_state(recipe: str, value: bool, dataset: str) -> None:
    if dataset is None:
        return
    key = selected_recipes_key(dataset=dataset)
    if key not in st.session_state:
        st.session_state[key] = set()
    if value:
        st.session_state[key].add(recipe)
    else:
        st.session_state[key].discard(recipe)


### Get/Set Page Loaded

def page_loaded_key(page:str) -> str:
    return f"page_{page}"

def get_page_loaded(page: str) -> bool:
    key = page_loaded_key(page=page)
    return st.session_state.get(key, False)

def set_page_loaded(page: str) -> None:
    key = page_loaded_key(page=page)
    st.session_state[key] = True

def clear_page_loaded(page: str) -> None:
    key = page_loaded_key(page=page)
    if key in st.session_state:
        del st.session_state[key]

### Get/Set Data Timestamp

def data_timestamp_key() -> str:
    return "data_timestamp"

def get_data_timestamp() -> float:
    key = data_timestamp_key()
    return st.session_state.get(key, 0.0)

def set_data_timestamp() -> None:
    key = data_timestamp_key()
    st.session_state[key] = time.time()


### Get/Set Page Item

def get_page_item(key: str) -> Any | None:
    if key in st.session_state:
        return st.session_state[key]
    return None

def set_page_item(key: str, value: Any) -> None:
    st.session_state[key] = value

def set_page_item_if_empty(key: str, value: Any) -> None:
    if key not in st.session_state:
        st.session_state[key] = value
