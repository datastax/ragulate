import json
import sqlite3
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Set, Tuple

import pandas as pd
from pandas import Index

from ragulate.datasets import find_dataset

import sys

def print_err(any: Any) -> None:
    print(any, file=sys.stderr)


def get_conn(recipe: str) -> sqlite3.Connection:
    # Connect to the database in read-only mode using URI
    return sqlite3.connect(f"file:{recipe}.sqlite?mode=ro", uri=True)


@contextmanager
def query_database(recipe: str, query: str) -> Generator[sqlite3.Cursor, None, None]:
    # Connect to the database in read-only mode using URI
    conn = get_conn(recipe=recipe)

    try:
        cursor = conn.cursor()
        cursor.execute(query)
        yield cursor
    finally:
        # Ensure the connection is closed when the generator is done
        conn.close()


def get_datasets_and_metadata(recipe: str) -> Dict[str, Dict[str, Any]]:
    query = """
        SELECT
            app_id as dataset,
            json_extract(app_json, '$.metadata') AS metadata
        FROM
            trulens_apps;
    """

    results: Dict[str, Dict[str, Any]] = {}
    with query_database(recipe=recipe, query=query) as cursor:
        for row in cursor.fetchall():
            results[row[0]] = json.loads(row[1])

    return results


def get_metadata_options_for_recipe(recipe: str, dataset: str) -> Dict[str, List[Any]]:
    query = f"""
        SELECT
            json_extract(record_json, '$.meta') as metadata
        FROM
            trulens_records
        WHERE
            app_id = "{dataset}"
    """
    unique_values = defaultdict(set)
    with query_database(recipe=recipe, query=query) as cursor:
        while True:
            rows = cursor.fetchmany(100)  # Fetch 100 rows at a time
            if not rows:
                break
            for row in rows:
                metadata = json.loads(row[0])
                for key, value in metadata.items():
                    unique_values[key].add(value)

    # Convert sets to lists
    return {str(key): list(values) for key, values in unique_values.items()}


def get_data_for_recipe(
    recipe: str,
    dataset: str,
    metadata_filter: Dict[str, Any] = {},
    include_in_and_out: bool = False,
) -> Tuple[pd.DataFrame, List[str]]:
    conn = get_conn(recipe=recipe)

    try:
        feedbacks = []
        feedbacks_query = f"""
            SELECT DISTINCT
                json_extract(feedback_json, '$.supplied_name') as name
            FROM
                trulens_feedback_defs
            """
        cursor = conn.cursor()
        cursor.execute(feedbacks_query)
        for row in cursor.fetchall():
            feedbacks.append(row[0])

        cursor.close()

        selects = [
            "r.record_id",
            "json_extract(r.record_json, '$.meta') AS metadata",
            "json_extract(r.cost_json, '$.n_tokens') AS total_tokens",
            "(julianday(json_extract(r.perf_json, '$.end_time')) - julianday(json_extract(r.perf_json, '$.start_time'))) * 86400 AS latency",
        ]

        if include_in_and_out:
            selects.extend(["r.input", "r.output"])

        joins = []
        for i, feedback in enumerate(feedbacks):
            selects.append(f"f{i}.result AS {feedback}")
            joins.append(
                f"LEFT JOIN trulens_feedbacks f{i} ON r.record_id = f{i}.record_id AND f{i}.status = 'done' AND f{i}.name = '{feedback}'"
            )

        wheres = [f"r.app_id = '{dataset}'"]

        for key, value in metadata_filter.items():
            wheres.append(f"json_extract(r.record_json, '$.meta.{key}') = '{value}'")

        chart_data_query = f"""
            SELECT
                {',\n                '.join(selects)}
            FROM
                trulens_records r
                {'\n                '.join(joins)}
            WHERE
                {'\n                AND '.join(wheres)}
            """

        return pd.read_sql_query(sql=chart_data_query, con=conn), feedbacks
    finally:
        conn.close()


def get_details_for_record(recipe: str, record_id: str) -> Dict[str, Any]:
    conn = get_conn(recipe=recipe)

    try:
        contexts_query = f"""
            SELECT
                json_extract(record_json, '$.calls') AS calls
            FROM
                trulens_records
            WHERE
                record_id = '{record_id}'
            """

        cursor = conn.cursor()
        cursor.execute(contexts_query)
        context_calls = cursor.fetchone()

        contexts: List[Any] = []
        if context_calls is not None:
            for call in json.loads(context_calls[0]):
                returns = call.get("rets", {})
                if isinstance(returns, dict):
                    for key in returns.keys():
                        if isinstance(returns[key], list):
                            contexts = returns[key]
                            break
                if len(contexts) > 0:
                    break
        cursor.close

        calls_query = f"""
            SELECT
                json_extract(value, '$.meta.reason') as reason,
                json_extract(value, '$.meta.reasons') as reasons,
                json_extract(value, '$.args.context') as context,
                json_extract(value, '$.ret') as score,
                name
            FROM
                trulens_feedbacks,
                json_each(calls_json, '$.calls')
            WHERE
                record_id = '{record_id}'
            """
        cursor = conn.cursor()
        cursor.execute(calls_query)

        calls: Dict[str, List[Dict[str, Any]]] = {}

        for call in cursor.fetchall():
            reason = call[0]
            reasons = call[1]
            context = call[2]
            score = call[3]
            name = call[4]
            if name not in calls:
                calls[name] = []
            calls[name].append(
                {
                    "reason": reason,
                    "reasons": reasons,
                    "context": context,
                    "score": score,
                }
            )

        return {
            "contexts": contexts,
            "calls": calls,
        }

    finally:
        conn.close()


DataFrameList = List[pd.DataFrame]
FeedbacksList = List[List[str]]


def split_into_dict(text: str, keys: List[str]) -> Dict[str, str]:
    # Create a dictionary to hold the results
    result_dict = {}

    # Start with the full text
    remaining_text = text

    # Iterate over the keys
    for i, key in enumerate(keys):
        # Find the start position of the current key
        key_position = remaining_text.find(key + ":")
        if key_position == -1:
            continue

        # Find the end position of the current value
        if i < len(keys) - 1:
            next_key_position = remaining_text.find(keys[i + 1] + ":")
        else:
            next_key_position = len(remaining_text)

        # Extract the value for the current key
        value = remaining_text[key_position + len(key) + 1 : next_key_position].strip()

        # Add the key-value pair to the dictionary
        result_dict[key] = value

        # Update the remaining text
        remaining_text = remaining_text[next_key_position:]

    return result_dict


def find_common_strings(list_of_lists: List[List[str]]) -> List[str]:
    # Convert each list to a set
    sets = [set(lst) for lst in list_of_lists]

    # Find the intersection of all sets
    common_strings = set.intersection(*sets)

    # Convert the set back to a list (if needed)
    return list(common_strings)


def get_compare_data(
    recipes: List[str], dataset: str, metadata_filter: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[str]]:
    df_list: List[pd.DataFrame] = []
    feedbacks_list: List[List[str]] = []

    for recipe in recipes:
        df, feedbacks = get_data_for_recipe(
            recipe=recipe,
            dataset=dataset,
            metadata_filter=metadata_filter,
            include_in_and_out=True,
        )
        df_list.append(df)
        feedbacks_list.append(feedbacks)

    feedbacks = find_common_strings(feedbacks_list)

    for i, (df, recipe) in enumerate(zip(df_list, recipes)):
        if i > 0:
            df.drop(columns=["metadata"], inplace=True)

        df.columns = Index(
            [
                f"{col}_{recipe}" if col not in ["input", "metadata"] else col
                for col in df.columns
            ]
        )

    combined_df = df_list[0]
    for df in df_list[1:]:
        combined_df = combined_df.merge(df, on="input", how="outer")

    ground_truths: Dict[str, str] = {}
    for query_response in find_dataset(name=dataset).get_golden_set():
        ground_truths[f"\"{query_response["query"]}\""] = query_response["response"]

    combined_df["ground_truth"] = combined_df["input"].map(ground_truths)

    columns_to_diff = feedbacks + ["total_tokens", "latency"]

    # If there are exactly two dataframes, calculate the differences
    if len(df_list) == 2:
        for col in columns_to_diff:
            combined_df[f"{col}__diff"] = (
                combined_df[f"{col}_{recipes[0]}"] - combined_df[f"{col}_{recipes[1]}"]
            )

    # Reorder the columns
    output_columns = [f"output_{recipe}" for recipe in recipes]
    remaining_columns = sorted(
        [
            col
            for col in combined_df.columns
            if col not in ["input", "ground_truth"] + output_columns
        ]
    )

    combined_df = combined_df[
        ["input", "ground_truth"] + output_columns + remaining_columns
    ]

    print_err(f"column types for recipe {recipe}:\n {combined_df.dtypes}")

    return combined_df, columns_to_diff


def get_detail_data(
    record_ids: List[str], recipes: List[str]
) -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    for record_id, recipe in zip(record_ids, recipes):
        results[recipe] = get_details_for_record(record_id=record_id, recipe=recipe)
    return results


def get_chart_data(
    recipes: List[str], dataset: str, metadata_filter: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[str]]:
    df_all = pd.DataFrame()

    all_feedbacks: Set[str] = set()

    for recipe in recipes:
        df, feedbacks = get_data_for_recipe(
            recipe=recipe, dataset=dataset, metadata_filter=metadata_filter
        )
        df["recipe"] = recipe
        df["dataset"] = dataset

        # set negative values to None
        for feedback in feedbacks:
            df.loc[df[feedback] < 0, feedback] = None

        df_all = pd.concat([df_all, df], axis=0, ignore_index=True)
        all_feedbacks = all_feedbacks.union(feedbacks)

    reset_df = df_all.reset_index(drop=True)

    return reset_df, sorted(list(all_feedbacks))


def get_metadata_options(recipes: List[str], dataset: str) -> Dict[str, Set[Any]]:
    metadata_options: Dict[str, Set[Any]] = {}

    for recipe in recipes:
        options = get_metadata_options_for_recipe(recipe=recipe, dataset=dataset)
        for key, values in options.items():
            if key not in metadata_options:
                metadata_options[key] = set(values)
            else:
                metadata_options[key] = metadata_options[key].union(values)

    return metadata_options
