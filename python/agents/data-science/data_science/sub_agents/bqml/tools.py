from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import os
from google.cloud import bigquery
from vertexai import rag

def check_bq_models(dataset_id: str) -> str:
    """Lists models in a BigQuery dataset and returns them as a string.

    Args:
        dataset_id: The ID of the BigQuery dataset (e.g., "project.dataset").

    Returns:
        A string representation of a list of dictionaries, where each dictionary
        contains the 'name' and 'type' of a model in the specified dataset.
        Returns an empty string "[]" if no models are found.
    """
    try:
        client = bigquery.Client()
        models = client.list_models(dataset_id)
        model_list = []
        print(f"Models contained in '{dataset_id}':")
        for model in models:
            model_id = model.model_id
            model_type = model.model_type
            model_list.append({'name': model_id, 'type': model_type})
        return str(model_list)
    except Exception as e:
        return f'An error occurred: {e!s}'

@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
def rag_response(query: str) -> str:
    """Retrieves contextually relevant information from a RAG corpus.

    Args:
        query (str): The query string to search within the corpus.

    Returns:
        vertexai.rag.RagRetrievalQueryResponse: The response containing retrieved
        information from the corpus.
    """
    corpus_name = os.getenv('BQML_RAG_CORPUS_NAME')
    rag_retrieval_config = rag.RagRetrievalConfig(top_k=3, filter=rag.Filter(vector_distance_threshold=0.5))
    response = rag.retrieval_query(rag_resources=[rag.RagResource(rag_corpus=corpus_name)], text=query, rag_retrieval_config=rag_retrieval_config)
    return str(response)