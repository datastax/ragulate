import asyncio
import json
from os import path

from .base_dataset import BaseDataset, QueryItem


class CragDataset(BaseDataset):
    _subset_kinds: list[str] = [
        "aggregation",
        "comparison",
        "false_premise",
        "multi-hop",
        "post-processing",
        "set",
        "simple_w_condition",
        "simple",
    ]

    def __init__(self, dataset_name: str, root_storage_path: str = "datasets"):
        super().__init__(dataset_name=dataset_name, root_storage_path=root_storage_path)

    def sub_storage_path(self) -> str:
        return path.join("crag", self.name)

    def download_dataset(self) -> None:
        if self.name == "task_1":
            urls = [
                "https://github.com/epinzur/crag_dataset/raw/main/task_1_dev_v4/html_documents.jsonl.bz2",
                "https://github.com/epinzur/crag_dataset/raw/main/task_1_dev_v4/parsed_documents.jsonl.bz2",
                "https://github.com/epinzur/crag_dataset/raw/main/task_1_dev_v4/questions.jsonl.bz2",
            ]
            output_files = [
                path.join(self.storage_path(), "html_documents.jsonl"),
                path.join(self.storage_path(), "parsed_documents.jsonl"),
                path.join(self.storage_path(), "questions.jsonl"),
            ]
            tasks = [
                self._download_and_decompress(
                    url=url, output_file_path=output_file, force=False
                )
                for url, output_file in zip(urls, output_files, strict=False)
            ]
            asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
        else:
            raise NotImplementedError(f"Crag download not supported for {self.name}")

    def get_source_file_paths(self) -> list[str]:
        raise NotImplementedError("Crag source files are not yet supported")

    def _load_query_items_and_golden_set(self) -> None:
        """Loads query_items and golden_set"""
        for subset in self.subsets:
            if subset not in self._subset_kinds:
                raise ValueError(
                    f"Subset: {subset} doesn't exist in dataset {self.name}. Choices are {self._subset_kinds}"
                )

        json_path = path.join(self.storage_path(), "questions.jsonl")
        with open(json_path) as f:
            for line in f:
                data = json.loads(line.strip())
                kind = data.get("question_type")

                if len(self.subsets) > 0 and kind not in self.subsets:
                    continue

                query = data.get("query")
                answer = data.get("answer")
                del data["query"]
                del data["answer"]
                if query is not None and answer is not None:
                    self._query_items.append(
                        QueryItem(
                            query=query,
                            metadata=data,
                        )
                    )
                    self._golden_set.append({"query": query, "response": answer})
