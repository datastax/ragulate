from .base_dataset import BaseDataset, QueryItem


class TestDataset(BaseDataset):
    def sub_storage_path(self) -> str:
        return "sub_storage_path"

    def download_dataset(self) -> None:
        pass

    def get_source_file_paths(self) -> list[str]:
        return []

    def _load_query_items_and_golden_set(self) -> None:
        self._query_items = [
            QueryItem("Quéry 1", metadata={}),
            QueryItem("Query 2", metadata={}),
            QueryItem("Query 3", metadata={}),
            QueryItem("Query 4", metadata={}),
        ]
        self._golden_set = [
            {"query": "Query 1", "response": "Response 1"},
            {"query": "Query 2", "response": "Response 2"},
            {"query": "Query 3", "response": "Response 3"},
            {"query": "Query 4", "response": "Response 4"},
        ]
