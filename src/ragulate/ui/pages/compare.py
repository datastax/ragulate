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


import sys

import pandas as pd
import streamlit as st
from ragulate.data import get_compare_data, get_detail_data, split_into_dict
from ragulate.ui import state
from ragulate.ui.column import Column, get_column_defs
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode
from streamlit_extras.switch_page_button import switch_page


def print_err(any: Any) -> None:
    print(any, file=sys.stderr)


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
    compare_df, data_cols = get_data(
        recipes=recipes, dataset=dataset, filter=filter, timestamp=0
    )

    columns: Dict[str, Column] = {}

    columns["Query"] = Column(field="input", style={"word-break": "break-word"})
    columns["Answer"] = Column()
    columns["Metadata"] = Column(field=f"metadata", hide=True)

    for recipe in recipes:
        columns["Answer"].children[recipe] = Column(
            field=f"output_{recipe}", width=400, style={"word-break": "break-word"}
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
        record_ids: List[str] = []
        for recipe in recipes:
            record_ids.append(selected_rows[f"record_id_{recipe}"][0])

        detail_data = get_detail_data(recipes=recipes, record_ids=record_ids)

        # Start the record specific section
        st.divider()

        st.subheader(f"Query")
        st.write(selected_rows["input"][0])

        st.caption("metadata:")
        metadata = selected_rows[f"metadata"][0]
        st.json(metadata)

        st.subheader(f"Ground Truth")
        st.write(selected_rows["ground_truth"][0])

        # make markdwon table to show Answer and Scores

        table: Dict[str, List[str]] = {"Answer": []}
        for recipe in recipes:
            answer = selected_rows[f"output_{recipe}"][0]
            table["Answer"].append(answer)
            for data_col in data_cols:
                if data_col not in table:
                    table[data_col] = []
                value = selected_rows[f"{data_col}_{recipe}"][0]
                if value is None:
                    table[data_col].append("")
                elif data_col != "total_tokens":
                    table[data_col].append("{:.2f}".format(value))
                else:
                    table[data_col].append(f"{value}")

        markdown_lines = ["|      |" + " | ".join(recipes) + "|"]
        markdown_lines.append("|----" * (len(recipes) + 1) + "|")

        for legend, values in table.items():
            line = f"| {legend} | "
            for value in values:
                line += f" {value} |"
            markdown_lines.append(line)

        st.subheader(f"Results")

        st.markdown("\n".join(markdown_lines))

        st.subheader(f"Contexts")
        context_indexes: Dict[str, Dict[str, int]] = {}
        context_cols = st.columns(len(recipes))
        for i, recipe in enumerate(recipes):
            context_indexes[recipe] = {}
            try:
                for j, context in enumerate(detail_data[recipe]["contexts"]):
                    context_cols[i].caption(f"Chunk: {j + 1}")
                    context_indexes[recipe][context["page_content"]] = j
                    with context_cols[i].popover(
                        f"{json.dumps(context['page_content'][0:200])}..."
                    ):
                        st.caption("Metadata")
                        st.json(context["metadata"], expanded=False)
                        st.caption("Content")
                        st.write(context["page_content"])
            except (TypeError, KeyError):
                continue

        st.subheader(f"Reasons")

        with st.expander(f"Answer Relevance"):
            reason_cols = st.columns(len(recipes))
            for i, recipe in enumerate(recipes):
                try:
                    calls = detail_data[recipe]["calls"]["answer_relevance"]

                    if len(calls) > 0:
                        call = calls[0]
                        reason = split_into_dict(
                            call["reason"], ["Criteria", "Supporting Evidence"]
                        )
                        reason["score"] = call["score"]

                        reason_cols[i].json(reason)
                except (TypeError, KeyError):
                    continue

        with st.expander(f"Context Relevance"):
            reason_cols = st.columns(len(recipes))
            for i, recipe in enumerate(recipes):
                try:
                    calls = detail_data[recipe]["calls"]["context_relevance"]
                    # reason_cols[i].write(calls)

                    context_reasons: Dict[int, Dict[str, Any]] = {}

                    for call in calls:
                        context_index = context_indexes[recipe][call["context"]]
                        reason = split_into_dict(
                            call["reason"], ["Criteria", "Supporting Evidence"]
                        )
                        reason["score"] = call["score"]
                        context_reasons[context_index] = reason
                    reason_cols[i].json(context_reasons)
                except (TypeError, KeyError):
                    continue

        with st.expander(f"Groundedness"):
            reason_cols = st.columns(len(recipes))
            for i, recipe in enumerate(recipes):
                try:
                    calls = detail_data[recipe]["calls"]["groundedness"]

                    reasons = []
                    for call in calls:
                        del call["reason"]
                        del call["context"]
                        reasons.append(call)

                    reason_cols[i].json(reasons)
                except (TypeError, KeyError):
                    continue
