from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
from tenacity import retry, wait_exponential, stop_after_attempt
import os
from pathlib import Path
import vertexai
from dotenv import load_dotenv, set_key
from vertexai import rag
env_file_path = Path(__file__).parent.parent.parent / '.env'
print(env_file_path)
load_dotenv(dotenv_path=env_file_path)
PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
corpus_name = os.getenv('BQML_RAG_CORPUS_NAME')
display_name = 'bqml_referenceguide_corpus'
paths = ['gs://cloud-samples-data/adk-samples/data-science/bqml']
vertexai.init(project=PROJECT_ID, location='us-central1')

def create_RAG_corpus():
    embedding_model_config = rag.RagEmbeddingModelConfig(vertex_prediction_endpoint=rag.VertexPredictionEndpoint(publisher_model='publishers/google/models/text-embedding-005'))
    backend_config = rag.RagVectorDbConfig(rag_embedding_model_config=embedding_model_config)
    bqml_corpus = rag.create_corpus(display_name=display_name, backend_config=backend_config)
    write_to_env(bqml_corpus.name)
    return bqml_corpus.name

def ingest_files(corpus_name):
    transformation_config = rag.TransformationConfig(chunking_config=rag.ChunkingConfig(chunk_size=512, chunk_overlap=100))
    rag.import_files(corpus_name, paths, transformation_config=transformation_config, max_embedding_requests_per_min=1000)
    rag.list_files(corpus_name)

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

def write_to_env(corpus_name):
    """Writes the corpus name to the specified .env file.

    Args:
        corpus_name: The name of the corpus to write.
    """
    load_dotenv(env_file_path)
    set_key(env_file_path, 'BQML_RAG_CORPUS_NAME', corpus_name)
    print(f"BQML_RAG_CORPUS_NAME '{corpus_name}' written to {env_file_path}")
if __name__ == '__main__':
    corpus_name = os.getenv('BQML_RAG_CORPUS_NAME')
    print('Creating the corpus.')
    corpus_name = create_RAG_corpus()
    print(f'Corpus name: {corpus_name}')
    print(f'Importing files to corpus: {corpus_name}')
    ingest_files(corpus_name)
    print(f'Files imported to corpus: {corpus_name}')