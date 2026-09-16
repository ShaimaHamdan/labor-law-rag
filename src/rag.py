import re
from collections import OrderedDict

from .config import Settings
from .data_loader import JsonlDataLoader
from .embedding import OllamaEmbedding
from .llm import INSUFFICIENT_ANSWER, OllamaLLM
from .retriever import Retriever
from .vector_store import FaissVectorStore


class RAG:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.from_root()
        embedder = OllamaEmbedding(self.settings.embedding_model, self.settings.ollama_host)
        llm = OllamaLLM(
            self.settings.llm_model,
            self.settings.ollama_host,
            max_output_tokens=self.settings.max_output_tokens,
        )
        metadata_loader = JsonlDataLoader(self.settings.metadata_file)
        vector_store = FaissVectorStore(self.settings.index_file)
        self.retriever = Retriever(
            vector_store,
            metadata_loader,
            embedder,
            llm,
            llm,
            candidate_k=self.settings.candidate_k,
        )
        self.llm = llm
        self._cache = OrderedDict()

    def query(self, query, progress_callback=None):
        cache_key = " ".join(query.split()).casefold()
        if cache_key in self._cache:
            result = self._cache.pop(cache_key)
            self._cache[cache_key] = result
            print("Returning cached RAG response.")
            if progress_callback:
                progress_callback(100)
            return result

        chunks = self.retriever.retrieve(
            query,
            self.settings.top_k,
            progress_callback=progress_callback,
        )
        if progress_callback:
            progress_callback(75)
        answer = self.llm.generate_answer(query, chunks)
        if progress_callback:
            progress_callback(100)
        if answer == INSUFFICIENT_ANSWER:
            result = (answer, [])
            self._remember(cache_key, result)
            return result

        cited_numbers = {
            int(number)
            for number in re.findall(r"\[المصدر\s+(\d+)\]", answer)
        }
        if not cited_numbers:
            result = (INSUFFICIENT_ANSWER, [])
            self._remember(cache_key, result)
            return result

        cited_chunks = [
            chunk for number, chunk in enumerate(chunks, start=1)
            if number in cited_numbers
        ]
        if not cited_chunks or cited_numbers - set(range(1, len(chunks) + 1)):
            result = (INSUFFICIENT_ANSWER, [])
            self._remember(cache_key, result)
            return result

        factual_lines = [
            line.strip()
            for line in answer.splitlines()
            if line.strip() and not line.strip().startswith("[")
        ]
        if any("[المصدر" not in line for line in factual_lines):
            result = (INSUFFICIENT_ANSWER, [])
            self._remember(cache_key, result)
            return result

        sources = [
            {
                "article": chunk["sequence"],
                "source": chunk.get("source", ""),
                "source_url": chunk.get("source_url", ""),
                "text": chunk.get("text", ""),
            }
            for chunk in cited_chunks
        ]
        display_answer = re.sub(r"\s*\[المصدر\s+\d+\]", "", answer).strip()
        result = (display_answer, sources)
        self._remember(cache_key, result)
        return result

    def _remember(self, key, value):
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self.settings.cache_size:
            self._cache.popitem(last=False)
