# RAGulate

A tool for evaluating RAG pipelines

![ragulate_logo](https://raw.githubusercontent.com/datastax/ragulate/main/images/logo_smaller.png)

## The Metrics

The RAGulate currently reports 4 relevancy metrics: Answer Correctness, Answer Relevance, Context Relevance, and Groundedness.


![metrics_diagram](https://raw.githubusercontent.com/datastax/ragulate/main/images/metrics.png)

* Answer Correctness
  * How well does the generated answer match the ground-truth answer?
  * This confirms how well the full system performed.
* Answer Relevance
  * Is the generated answer relevant to the query?
  * This shows if the LLM is responding in a way that is helpful to answer the query.
* Context Relevance:
  * Does the retrieved context contain information to answer the query?
  * This shows how well the retrieval part of the process is performing.
* Groundedness:
  * Is the generated response supported by the context?
  * Low scores here indicate that the LLM is hallucinating.

## Example Output

The tool outputs results as images like this:

![example_output](https://raw.githubusercontent.com/datastax/ragulate/main/images/example.png)

These images show distribution box plots of the metrics for different test runs.

## Installation

```sh
pip install ragulate
```

## Initial Setup

1. Set your environment variables or create a `.env` file. You will need to set `OPENAI_API_KEY` and
  any other environment variables needed by your ingest and query pipelines.

1. Wrap your ingest pipeline in a single python method. The method should take a `file_path` parameter and
  any other variables that you will pass during your experimentation. The method should ingest the passed
  file into your vector store.

   See the `ingest()` method in [open_ai_chunk_size_and_k.py](examples/open_ai_chunk_size_and_k.py) as an example.
   This method configures an ingest pipeline using the parameter `chunk_size` and ingests the file passed.

1. Wrap your query pipeline in a single python method, and return it. The method should have parameters for
  any variables that you will pass during your experimentation. Currently only LangChain LCEL query pipelines
  are supported.

   See the `query()` method in [open_ai_chunk_size_and_k.py](examples/open_ai_chunk_size_and_k.py) as an example.
   This method returns a LangChain LCEL pipeline configured by the parameters `chunk_size` and `k`.

Note: It is helpful to have a `**kwargs` param in your pipeline method definitions, so that if extra params
  are passed, they can be safely ignored.

## Usage

### Summary

```sh
usage: ragulate [-h] {download,ingest,query,compare,run,debug} ...

RAGu-late CLI tool.

options:
  -h, --help            show this help message and exit

commands:
  {download,ingest,query,compare,run,debug}
    download            Download a dataset
    ingest              Run an ingest pipeline
    query               Run a query pipeline
    compare             Compare results from 2 (or more) recipes
    debug               Show the tru-lens dashboard to debug a recipe.
```

#### Query

```sh
usage: ragulate query [-h] [-n NAME] -s SCRIPT -m METHOD [--var-name VAR_NAME] [--var-value VAR_VALUE] [--dataset DATASET] [--subset SUBSET]
                      [--sample SAMPLE] [--seed SEED] [--restart] [--provider {OpenAI,AzureOpenAI,HuggingFace}] [--model MODEL]

options:
  -h, --help            show this help message and exit
  -n NAME, --name NAME  A unique name for the query pipeline
  -s SCRIPT, --script SCRIPT
                        The path to the python script that contains the query method
  -m METHOD, --method METHOD
                        The name of the method in the script to run query
  --var-name VAR_NAME   The name of a variable in the query script. This should be paired with a `--var-value` argument and can be passed
                        multiple times.
  --var-value VAR_VALUE
                        The value of a variable in the query script. This should be paired with a `--var-name` argument and can be passed
                        multiple times.
  --dataset DATASET     The name of a dataset to query. This can be passed multiple times.
  --subset SUBSET       The subset of the dataset to query. Only valid when a single dataset is passed.
  --sample SAMPLE       A decimal percentage of the queries to sample for the test. Default is 1.0.
  --seed SEED           Random seed to use for query sampling. Ensures reproducibility of tests.
  --restart             Flag to restart the query process instead of resuming. WARNING: this will delete all existing data for this query name,
                        not just the data for the tagged datasets.
  --provider {OpenAI,AzureOpenAI,HuggingFace}
                        The name of the LLM Provider to use for Evaluation.
  --model MODEL         The name or id of the LLM model or deployment to use for Evaluation. Generally used in combination with the '--provider'
                        param.
```

### Example

For the examples below, we will use the example experiment [open_ai_chunk_size_and_k.py](examples/open_ai_chunk_size_and_k.py)
and see how the RAG metrics change for changes in `chunk_size` and `k` (number of documents retrieved).


1. Download a dataset. See available datasets here: https://llamahub.ai/?tab=llama_datasets
  * If you are unsure where to start, recommended datasets are:
    * `BraintrustCodaHelpDesk`
    * `BlockchainSolana`

    Examples:
    * `ragulate download -k llama BraintrustCodaHelpDesk`
    * `ragulate download -k llama BlockchainSolana`

2. Ingest the datasets using different methods:

    Examples:
    * Ingest with `chunk_size=200`:
      ```
      ragulate ingest -n chunk_size_200 -s open_ai_chunk_size_and_k.py -m ingest \
      --var-name chunk_size --var-value 200 --dataset BraintrustCodaHelpDesk --dataset BlockchainSolana
      ```
    * Ingest with `chunk_size=100`:
      ```
      ragulate ingest -n chunk_size_100 -s open_ai_chunk_size_and_k.py -m ingest \
      --var-name chunk_size --var-value 100 --dataset BraintrustCodaHelpDesk --dataset BlockchainSolana
      ```

    Alternatively, do your ingestion manually without Ragulate.

3. Run query and evaluations on the datasets using methods:

    Examples:
    * Query with `chunk_size=200` and `k=2`
      ```
      ragulate query -n chunk_size_200_k_2 -s open_ai_chunk_size_and_k.py -m query_pipeline \
      --var-name chunk_size --var-value 200  --var-name k --var-value 2 --dataset BraintrustCodaHelpDesk --dataset BlockchainSolana
      ```

    * Query with `chunk_size=100` and `k=2`
      ```
      ragulate query -n chunk_size_100_k_2 -s open_ai_chunk_size_and_k.py -m query_pipeline \
      --var-name chunk_size --var-value 100  --var-name k --var-value 2 --dataset BraintrustCodaHelpDesk --dataset BlockchainSolana
      ```

    * Query with `chunk_size=200` and `k=5`
      ```
      ragulate query -n chunk_size_200_k_5 -s open_ai_chunk_size_and_k.py -m query_pipeline \
      --var-name chunk_size --var-value 200  --var-name k --var-value 5 --dataset BraintrustCodaHelpDesk --dataset BlockchainSolana
      ```

    * Query with `chunk_size=100` and `k=5`
      ```
      ragulate query -n chunk_size_100_k_5 -s open_ai_chunk_size_and_k.py -m query_pipeline \
      --var-name chunk_size --var-value 100  --var-name k --var-value 5 --dataset BraintrustCodaHelpDesk --dataset BlockchainSolana
      ```

4. Use the UI to explore your experiments `ragulate-ui`

  * Select your dataset
  * Choose which recipes to compare
  * Optionally filter the datasets with 'Filter'
  * View charts with 'Chart'
  * Compare responses side-by-side with 'Compare'


## Current Limitations

* Only LangChain query pipelines are supported
* There is no way to specify which metrics to evaluate.

## Development

Note that this project uses [uv](https://docs.astral.sh/uv/) for package management. Install it with `make install-uv`.


## Deprecated

### Running via Config File

1. Create a yaml config file with a similar format to the example config: [example_config.yaml](examples/config.yaml).  This defines the same test as shown manually below.

1. Execute it with a single command:

    ```
    ragulate run example_config.yaml
    ```

    This will:
    * Download the test datasets
    * Run the ingest pipelines
    * Run the query pipelines
    * Output an analysis of the results.

### Performing comparisons via the CLI:

Example:
  ```
  ragulate compare -r chunk_size_100_k_2 -r chunk_size_200_k_2 -r chunk_size_100_k_5 -r chunk_size_200_k_5
  ```

This will output 2 png files. one for each dataset.
