from src.config import Settings
from src.data_loader import JsonlDataLoader
from src.embedding import OllamaEmbedding
from src.rag import RAG


SETTINGS = Settings.from_root()
INDEX_FILE = SETTINGS.index_file
META_FILE = SETTINGS.metadata_file
EMBED_MODEL = SETTINGS.embedding_model
LLM_MODEL = SETTINGS.llm_model
TOP_K = SETTINGS.top_k

_rag = RAG(SETTINGS)


def load_metadata():
    return JsonlDataLoader(META_FILE).load()


def get_embedding(text):
    return OllamaEmbedding(EMBED_MODEL, SETTINGS.ollama_host).embed(text)


def normalize_query(query):
    return _rag.llm.normalize(query)


def select_relevant_chunks(query, chunks):
    return _rag.llm.select(query, chunks)


def retrieve(query, k=TOP_K):
    return _rag.retriever.retrieve(query, k)


def generate_answer(query, chunks):
    return _rag.llm.generate_answer(query, chunks)


def rag_query(query, progress_callback=None):
    return _rag.query(query, progress_callback=progress_callback)


if __name__ == "__main__":
    import sys

    query = sys.argv[1] if len(sys.argv) > 1 else "إذا مات العامل ماذا يحدث لعقد العمل؟"
    answer, sources = rag_query(query)

    print("\n" + "=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(answer)
    print("\nSOURCES")
    print("-" * 60)

    for source in sources:
        print(f"Article: {source['article']}")
        print(f"Source: {source['source']}")
        print(f"URL: {source['source_url']}")
        print("-" * 60)
