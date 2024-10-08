import json
from os import path

import inflection
from llama_index.core.download.dataset import (
    LLAMA_DATASETS_LFS_URL,
    LLAMA_DATASETS_SOURCE_FILES_GITHUB_TREE_URL,
)
from llama_index.core.llama_dataset import download

from ..logging_config import logger
from .base_dataset import BaseDataset, QueryItem


class LlamaDataset(BaseDataset):
    _llama_datasets_lfs_url: str
    _llama_datasets_source_files_tree_url: str

    def __init__(self, dataset_name: str, root_storage_path: str = "datasets"):
        super().__init__(dataset_name=dataset_name, root_storage_path=root_storage_path)
        self._llama_datasets_lfs_url: str = LLAMA_DATASETS_LFS_URL
        self._llama_datasets_source_files_tree_url: str = (
            LLAMA_DATASETS_SOURCE_FILES_GITHUB_TREE_URL
        )

    def sub_storage_path(self) -> str:
        return "llama"

    def _get_dataset_path(self) -> str:
        folder = inflection.underscore(self.name)
        folder = folder.removesuffix("_dataset")
        return path.join(self.storage_path(), folder)

    def download_dataset(self) -> None:
        """Downloads a dataset locally"""
        download_dir = self._get_dataset_path()

        def download_by_name(name: str) -> None:
            download.download_llama_dataset(
                llama_dataset_class=name,
                download_dir=download_dir,
                llama_datasets_lfs_url=self._llama_datasets_lfs_url,
                llama_datasets_source_files_tree_url=self._llama_datasets_source_files_tree_url,
                show_progress=True,
                load_documents=False,
            )

        # to conform with naming scheme at LlamaHub
        name = self.name
        try:
            download_by_name(name=name)
        except:
            if not name.endswith("Dataset"):
                try:
                    download_by_name(name + "Dataset")
                except:
                    raise ValueError(f"Could not find {name} datset.")
            else:
                raise ValueError(f"Could not find {name} datset.")

        logger.info(f"Successfully downloaded {self.name} to {download_dir}")

    def get_source_file_paths(self) -> list[str]:
        """Gets a list of source file paths for for a dataset"""
        source_path = path.join(self._get_dataset_path(), "source_files")
        return self.list_files_at_path(path=source_path)

    def _load_query_items_and_golden_set(self) -> None:
        """Loads query_items and golden_set"""
        json_path = path.join(self._get_dataset_path(), "rag_dataset.json")
        with open(json_path) as f:
            examples = json.load(f)["examples"]
            for example in examples:
                self._query_items.append(QueryItem(query=example["query"], metadata={}))
                self._golden_set.append(
                    {
                        "query": example["query"],
                        "response": example["reference_answer"],
                    }
                )
