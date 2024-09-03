import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from ragulate.ui.state import set_data_timestamp


def write_button_row(current_page: str, disable_non_home: bool = False) -> None:
    colHome, colCompare, colChart, colFilter, colRefresh = st.columns(5)
    if colHome.button("home", disabled=current_page == "home"):
        switch_page("home")

    if colCompare.button(
        "compare", disabled=current_page == "compare" or disable_non_home
    ):
        switch_page("compare")

    if colChart.button("chart", disabled=current_page == "chart" or disable_non_home):
        switch_page("chart")

    if colFilter.button(
        "filter", disabled=current_page == "filter" or disable_non_home
    ):
        switch_page("filter")

    if colRefresh.button("refresh", disabled=False):
        set_data_timestamp()
