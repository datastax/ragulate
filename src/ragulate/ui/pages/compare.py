import asyncio
import json
import sys
from typing import Any, Dict, List, Set, Tuple

import pandas as pd
from pandas import Index
from typing_extensions import Generic, Protocol

sys.modules["pip._vendor.typing_extensions"] = sys.modules["typing_extensions"]

# https://github.com/jerryjliu/llama_index/issues/7244:
asyncio.set_event_loop(asyncio.new_event_loop())


import pandas as pd
import streamlit as st
from ragulate.ui import state
from ragulate.ui.column import Column, get_column_defs
from ragulate.ui.data import get_compare_data, get_metadata_options

from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
from streamlit_extras.switch_page_button import switch_page

PAGINATION_SIZE = 10
SELECT_ALL_TEXT = "<all>"

st.set_page_config(page_title="Ragulate - Compare", layout="wide")

numericColumnType = ["numericColumn", "numberColumnFilter"]


@st.cache_data
def get_data(
    recipes: List[str], dataset: str, filter: Dict[str, Any], timestamp: int
) -> Tuple[pd.DataFrame, List[str]]:
    return get_compare_data(recipes=recipes, dataset=dataset, metadata_filter=filter)

col1, col2 = st.columns(2)
if col1.button("home"):
    switch_page("home")

if col2.button("filter"):
    switch_page("filter")

recipes = list(state.get_selected_recipes())
dataset = state.get_selected_dataset()

if dataset is None or len(recipes) < 2:
    switch_page("home")
else:
    filter = state.get_metadata_filter()
    compare_df, data_cols = get_data(recipes=recipes, dataset=dataset, filter=filter, timestamp=0)

    columns: Dict[str, Column] = {}

    columns["Query"] = Column(field="input", style={"word-break": "break-word"})
    columns["Answer"] = Column()
    columns["Metadata"] = Column(field=f"metadata", hide=True)

    for recipe in recipes:
        columns["Answer"].children[recipe] = Column(
            field=f"output_{recipe}", width=400, style={"word-break": "break-word"}
        )
        columns[f"contexts_{recipe}"] = Column(field=f"contexts_{recipe}", hide=True)

        columns[f"answer_relevance_reason_{recipe}"] = Column(
            field=f"answer_relevance_reason_{recipe}", hide=True
        )
        columns[f"context_relevance_reasons_{recipe}"] = Column(
            field=f"context_relevance_reasons_{recipe}", hide=True
        )
        columns[f"groundedness_reasons_{recipe}"] = Column(
            field=f"groundedness_reasons_{recipe}", hide=True
        )

    columns["Answer"].children["Ground Truth"] = Column(
        field="ground_truth", width=400, style={"word-break": "break-word"}
    )

    for data_col in data_cols:
        columns[data_col] = Column()
        for recipe in recipes:
            columns[data_col].children[recipe] = Column(
                field=f"{data_col}_{recipe}",
                type=numericColumnType,
                width=(len(recipe) * 7) + 50,
            )
        if len(recipes) == 2:
            columns[data_col].children["Diff"] = Column(
                field=f"{data_col}__diff",
                type=numericColumnType,
                width=(len("Diff") * 7) + 50,
            )

    gb = GridOptionsBuilder.from_dataframe(compare_df)

    gb.configure_default_column(autoHeight=True, wrapText=True)
    gb.configure_pagination(
        paginationPageSize=PAGINATION_SIZE, paginationAutoPageSize=False
    )
    gb.configure_selection(selection_mode="single", pre_selected_rows=[0])

    gridOptions = gb.build()
    gridOptions["columnDefs"] = get_column_defs(columns=columns)
    with st.container():
        data = AgGrid(
            compare_df,
            gridOptions=gridOptions,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            allow_unsafe_jscode=True,
        )

        selected_rows = data.selected_rows
        selected_rows = pd.DataFrame(selected_rows)

    if len(selected_rows) == 0:
        st.write("Hint: select a row to display details of a record")

    else:
        # Start the record specific section
        st.divider()

        st.subheader(f"Query")
        st.write(selected_rows["input"][0])

        st.caption("metadata:")
        metadata = selected_rows[f"metadata"][0]
        st.json(metadata)

        st.subheader(f"Ground Truth")
        st.write(selected_rows["ground_truth"][0])

        table = {}
        for recipe in recipes:
            column_data = [selected_rows[f"output_{recipe}"][0]]
            for data_col in data_cols:
                column_data.append(selected_rows[f"{data_col}_{recipe}"][0])
            table[recipe] = column_data

        context_indexes: Dict[str, Dict[str, int]] = {}

        df = pd.DataFrame(table)
        df.index = Index(["Answer"] + data_cols)
        st.subheader(f"Results")
        st.table(df)

        st.subheader(f"Contexts")
        context_cols = st.columns(len(recipes))
        for i, recipe in enumerate(recipes):
            context_indexes[recipe] = {}
            try:
                for j, context in enumerate(selected_rows[f"contexts_{recipe}"][0]):
                    context_cols[i].caption(f"Chunk: {j + 1}")
                    context_indexes[recipe][context["page_content"]] = j
                    with context_cols[i].popover(
                        f"{json.dumps(context['page_content'][0:200])}..."
                    ):
                        st.caption("Metadata")
                        st.json(context["metadata"], expanded=False)
                        st.caption("Content")
                        st.write(context["page_content"])
            except TypeError:
                continue

        st.subheader(f"Reasons")

        with st.expander(f"Answer Relevance"):
            reason_cols = st.columns(len(recipes))
            for i, recipe in enumerate(recipes):
                reasons = selected_rows[f"answer_relevance_reason_{recipe}"][0]
                if reasons:
                    reason_cols[i].json(reasons)

        with st.expander(f"Context Relevance"):
            reason_cols = st.columns(len(recipes))
            for i, recipe in enumerate(recipes):
                try:
                    context_reasons: Dict[int, Dict[str, Any]] = {}
                    for context_reason in selected_rows[
                        f"context_relevance_reasons_{recipe}"
                    ][0]:
                        context_index = context_indexes[recipe][
                            context_reason["context"]
                        ]
                        context_reasons[context_index] = {
                            "score": context_reason["score"],
                            "reason": context_reason["reason"],
                        }
                    reason_cols[i].json(context_reasons)
                except TypeError:
                    continue

        with st.expander(f"Groundedness"):
            reason_cols = st.columns(len(recipes))
            for i, recipe in enumerate(recipes):
                try:
                    groundedness_reasons: Dict[str, Any] = {
                        "contexts": [],
                        "reasons": [],
                    }
                    for context in selected_rows[f"groundedness_reasons_{recipe}"][0][
                        "contexts"
                    ]:
                        groundedness_reasons["contexts"].append(
                            context_indexes[recipe][context]
                        )
                    groundedness_reasons["reasons"] = selected_rows[
                        f"groundedness_reasons_{recipe}"
                    ][0]["reasons"].split("\n\n")
                    reason_cols[i].json(groundedness_reasons)
                except TypeError:
                    continue
