from pathlib import Path

from ragulate.datasets import TestDataset
from ragulate.pipelines import QueryPipeline
from trulens_eval import TruBasicApp


def demo_pipeline(param1: str, param2: str) -> None:
    pass


class TestQueryPipeline:
    test_dataset = TestDataset(dataset_name="test_dataset")

    def test_no_filters(self) -> None:
        query_pipeline = QueryPipeline(
            recipe_name=":memory:",  # use in-memory database
            script_path=__file__,
            method_name="demo_pipeline",
            ingredients={"param1": "value1", "param2": "value2"},
            datasets=[self.test_dataset],
        )

        assert query_pipeline._total_queries == 4
        assert query_pipeline._finished_queries == 0
        assert query_pipeline._total_feedbacks == 4 * 4

        query_pipeline._tru.delete_singleton()

    def test_50_percent_sample(self) -> None:
        query_pipeline = QueryPipeline(
            recipe_name=":memory:",  # use in-memory database
            script_path=__file__,
            method_name="demo_pipeline",
            ingredients={"param1": "value1", "param2": "value2"},
            datasets=[self.test_dataset],
            sample_percent=0.5,
        )

        assert query_pipeline._total_queries == 2
        assert query_pipeline._finished_queries == 0
        assert query_pipeline._total_feedbacks == 4 * 2

        query_pipeline._tru.delete_singleton()

    def test_existing_completed_query(self) -> None:
        # remove db from previous run if exists
        Path("test_recipe.sqlite").unlink(missing_ok=True)

        setup_pipeline = QueryPipeline(
            recipe_name="test_recipe",
            script_path=__file__,
            method_name="demo_pipeline",
            ingredients={"param1": "value1", "param2": "value2"},
            datasets=[self.test_dataset],
        )

        recorder = TruBasicApp(
            lambda prompt: "response", app_id="test_dataset", feedbacks=[]
        )

        with recorder:
            recorder.app(self.test_dataset._query_items[0].query)

        setup_pipeline._tru.delete_singleton()

        query_pipeline = QueryPipeline(
            recipe_name="test_recipe",
            script_path=__file__,
            method_name="demo_pipeline",
            ingredients={"param1": "value1", "param2": "value2"},
            datasets=[self.test_dataset],
        )

        assert query_pipeline._total_queries == 4
        assert query_pipeline._finished_queries == 1
        assert query_pipeline._total_feedbacks == 4 * 4

        query_pipeline._tru.delete_singleton()

        Path("test_recipe.sqlite").unlink(missing_ok=True)

    def test_recipe_name_generation(self) -> None:
        # remove db from previous run if exists
        Path("param1_value1_param2_value2.sqlite").unlink(missing_ok=True)

        query_pipeline = QueryPipeline(
            script_path=__file__,
            method_name="demo_pipeline",
            ingredients={"param1": "value1", "param2": "value2"},
            datasets=[self.test_dataset],
        )

        assert query_pipeline.recipe_name == "param1_value1_param2_value2"

        Path("param1_value1_param2_value2.sqlite").unlink(missing_ok=True)
