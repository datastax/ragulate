import json
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
from pandas import Index

from ragulate.utils import get_tru

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


def extract_ground_truth(answer_correctness_calls: List[Dict[str, Any]]) -> str | None:
    if not answer_correctness_calls:
        return None

    try:
        first_call = answer_correctness_calls[0]
        ground_truth_response: str = first_call.get("meta", {}).get(
            "ground_truth_response"
        )
        return ground_truth_response
    except (IndexError, TypeError):
        return None


def extract_contexts(record_json: str) -> List[Any]:
    record = json.loads(record_json)
    calls = record.get("calls", [])
    for call in calls:
        returns = call.get("rets", {})
        if isinstance(returns, dict) and "context" in returns:
            context: List[Any] = returns["context"]
            return context
    return []

def extract_metadata(record_json: str) -> Dict[str,Any]:
    record = json.loads(record_json)
    return record.get("meta", [])


def extract_answer_relevance_reason(
    answer_relevance_calls: List[Dict[str, Any]],
) -> Optional[Dict[str, str]]:
    if not answer_relevance_calls:
        return None

    try:
        first_call = answer_relevance_calls[0]
        reason = first_call.get("meta", {}).get("reason")
        return split_into_dict(reason, ["Criteria", "Supporting Evidence"])
    except (IndexError, TypeError):
        return None


def extract_context_relevance_reasons(
    context_relevance_calls: List[Dict[str, Any]],
) -> Optional[List[Dict[str, Any]]]:
    reasons = []
    if isinstance(context_relevance_calls, list):
        for call in context_relevance_calls:
            reason = call.get("meta", {}).get("reason")
            reasons.append(
                {
                    "context": call.get("args", {}).get("context"),
                    "score": call.get("ret"),
                    "reason": split_into_dict(
                        reason, ["Criteria", "Supporting Evidence"]
                    ),
                }
            )
    return reasons if len(reasons) > 0 else None


def extract_groundedness_reasons(
    groundedness_calls: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if not groundedness_calls:
        return None

    try:
        first_call = groundedness_calls[0]

        return {
            "contexts": first_call.get("args", {}).get(
                "source", []
            ),  # list of contexts
            # string with format: `STATEMENT {n}:\nCriteria: {reason}\nSupporting Evidence: {evidence}\nScore: {score}`
            # where n doesn't seem to match with the number of contexts well.
            "reasons": first_call.get("meta", {}).get("reasons"),
        }
    except (IndexError, TypeError):
        return None


def find_common_strings(list_of_lists: List[List[str]]) -> List[str]:
    # Convert each list to a set
    sets = [set(lst) for lst in list_of_lists]

    # Find the intersection of all sets
    common_strings = set.intersection(*sets)

    # Convert the set back to a list (if needed)
    return list(common_strings)


def find_full_set_of_strings(list_of_lists: List[List[str]]) -> List[str]:
    # Convert each list to a set
    sets = [set(lst) for lst in list_of_lists]

    # Find the union of all sets
    full_set_of_strings = set.union(*sets)

    # Convert the set back to a list (if needed)
    return list(full_set_of_strings)

def get_dfs_and_feedbacks(recipes: List[str], dataset: str) -> Tuple[DataFrameList, FeedbacksList]:
    df_list: DataFrameList = []
    feedbacks_list: FeedbacksList = []
    for recipe in recipes:
        tru = get_tru(recipe_name=recipe)
        df, feedbacks = tru.get_records_and_feedback(app_ids=[dataset])
        df_list.append(df)
        feedbacks_list.append(feedbacks)
        tru.delete_singleton()
    return df_list, feedbacks_list

def filter_by_metadata(df: pd.DataFrame, filter_dict: Dict[str, Any]) -> pd.DataFrame:
    return df[df['metadata'].apply(lambda x: isinstance(x, dict) and all(x.get(k) == v for k, v in filter_dict.items()))]

def get_compare_data(
    recipes: List[str], dataset: str, metadata_filter: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[str]]:
    df_list, feedbacks_list = get_dfs_and_feedbacks(recipes=recipes, dataset=dataset)

    feedbacks = find_common_strings(feedbacks_list)

    # Columns: ['app_id', 'app_json', 'type', 'record_id', 'input', 'output',
    # 'tags', 'record_json', 'cost_json', 'perf_json', 'ts', 'context_relevance',
    # 'answer_relevance', 'answer_correctness', 'groundedness', 'context_relevance_calls',
    # 'answer_relevance_calls', 'answer_correctness_calls', 'groundedness_calls',
    # 'latency', 'total_tokens', 'total_cost']

    columns_to_drop = [
        "app_id",
        "app_json",
        "type",
        "record_id",
        "latency",
        "tags",
        "record_json",
        "cost_json",
        "perf_json",
        "ts",
        "total_cost",
    ]

    for feedback in find_full_set_of_strings(feedbacks_list):
        columns_to_drop.append(f"{feedback}_calls")

    columns_to_diff = feedbacks + ["total_tokens"]

    for i, (df, recipe) in enumerate(zip(df_list, recipes)):
        if i == 0:
            df["ground_truth"] = df["answer_correctness_calls"].apply(
                extract_ground_truth
            )
            df["metadata"] = df["record_json"].apply(extract_metadata)
        df["answer_relevance_reason"] = df["answer_relevance_calls"].apply(
            extract_answer_relevance_reason
        )
        df["context_relevance_reasons"] = df["context_relevance_calls"].apply(
            extract_context_relevance_reasons
        )
        df["groundedness_reasons"] = df["groundedness_calls"].apply(
            extract_groundedness_reasons
        )
        df["contexts"] = df["record_json"].apply(extract_contexts)

        df.drop(columns=columns_to_drop, inplace=True)
        df.columns = Index(
            [
                f"{col}_{recipe}" if col not in ["input", "ground_truth", "metadata"] else col
                for col in df.columns
            ]
        )

    combined_df = df_list[0]
    for df in df_list[1:]:
        combined_df = combined_df.merge(df, on="input", how="outer")

    combined_df = filter_by_metadata(df=combined_df, filter_dict=metadata_filter)

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

    return (combined_df, columns_to_diff)

def get_chart_data(
    recipes: List[str], dataset: str, metadata_filter: Dict[str, Any]
) -> Tuple[pd.DataFrame, List[str]]:
    df_list, feedbacks_list = get_dfs_and_feedbacks(recipes=recipes, dataset=dataset)

    feedbacks = find_common_strings(feedbacks_list)

    columns_to_keep = [
        *feedbacks,
        "record_id",
        "latency",
        "total_tokens",
        "total_cost",
    ]

    df_all = pd.DataFrame()

    for df, recipe in zip(df_list, recipes):
        columns_to_drop = [
            col for col in df.columns if col not in columns_to_keep
        ]

        df["metadata"] = df["record_json"].apply(extract_metadata)
        df = filter_by_metadata(df=df, filter_dict=metadata_filter)

        df = df.drop(columns=columns_to_drop)
        df["recipe"] = recipe
        df["dataset"] = dataset

        # set negative values to None
        for feedback in feedbacks:
            df.loc[df[feedback] < 0, feedback] = None

        df_all = pd.concat([df_all, df], axis=0, ignore_index=True)

    reset_df = df_all.reset_index(drop=True)

    return reset_df, sorted(list(set(feedbacks)))

def get_metadata_options(recipes: List[str], dataset: str) -> Dict[str, Set[Any]]:
    metadata_options: Dict[str, Set[Any]] = {}
    df_list, _ = get_dfs_and_feedbacks(recipes=recipes, dataset=dataset)

    for df in df_list:
        for json_record in df["record_json"]:
            metadata = extract_metadata(json_record)
            for key, value in metadata.items():
                if key not in metadata_options:
                    metadata_options[key] = {value}
                else:
                    metadata_options[key].add(value)

    return metadata_options

