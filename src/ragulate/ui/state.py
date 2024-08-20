import streamlit as st

from typing import Any, Set

def dataset_key() -> str:
    return f"home_dataset"

def recipe_key(recipe: str) -> str:
    return f"checkbox_{recipe}"

def get_selected_dataset() -> str | None:
    if "selected_dataset" not in st.session_state:
        st.session_state["selected_dataset"] = None
    return st.session_state["selected_dataset"]

def set_selected_dataset(dataset: str) -> None:
    st.session_state["selected_dataset"] = dataset

def clear_selected_recipes() -> None:
    st.session_state["selected_recipes"] = set()

def get_selected_recipes() -> Set[str]:
    if "selected_recipes" not in st.session_state:
        clear_selected_recipes()
    return st.session_state["selected_recipes"]

def get_recipe_state(recipe: str) -> bool:
    return recipe in get_selected_recipes()

def set_recipe_state(recipe: str, value: bool) -> None:
    if value:
        st.session_state["selected_recipes"].add(recipe)
    else:
        st.session_state["selected_recipes"].discard(recipe)

def set_page_item(key: str, value: Any) -> None:
    st.session_state[key] = value