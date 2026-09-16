import re


ARABIC_STOPWORDS = {
    "في", "من", "على", "عن", "إلى", "الى", "هل", "ما", "متى", "كيف",
    "هذا", "هذه", "ذلك", "تلك", "التي", "الذي", "هل", "يكون", "تكون",
}


def _terms(text):
    words = re.findall(r"[\w\u0600-\u06ff]+", text.lower())
    return {word for word in words if len(word) >= 3 and word not in ARABIC_STOPWORDS}


class Retriever:
    def __init__(self, vector_store, metadata_loader, embedder, query_normalizer, selector, candidate_k=15):
        self.vector_store = vector_store
        self.metadata_loader = metadata_loader
        self.embedder = embedder
        self.query_normalizer = query_normalizer
        self.selector = selector
        self.candidate_k = candidate_k

    def retrieve(self, query, k, progress_callback=None):
        print(f"\nOriginal query: {query}")
        search_query = (self.query_normalizer.normalize(query) or query).strip()
        if not search_query:
            print("No usable search query was produced.")
            return []
        print(f"Search query: {search_query}")
        print(f"Retrieving top {k} articles from {self.candidate_k} candidates...")

        metadata = self.metadata_loader.load()
        vector = self.embedder.as_vector(self.embedder.embed(search_query))
        candidate_k = max(k, self.candidate_k)
        distances, indices = self.vector_store.search(vector, candidate_k)

        chunks = []
        query_terms = _terms(search_query)
        result_indices = indices[0] if len(indices) else []
        result_distances = distances[0] if len(distances) else []
        for rank, index in enumerate(result_indices):
            if index == -1:
                continue
            if index >= len(metadata) or rank >= len(result_distances):
                continue
            item = metadata[index].copy()
            item["rank"] = rank + 1
            item["distance"] = float(distances[0][rank])
            item["lexical_score"] = len(query_terms & _terms(item["text"]))
            chunks.append(item)

        chunks.sort(key=lambda item: (-item["lexical_score"], item["distance"]))
        chunks = chunks[:k]
        if progress_callback:
            progress_callback(35)
        selected_chunks = self.selector.select(search_query, chunks)
        print(f"Selected {len(selected_chunks)} relevant articles.")
        if progress_callback:
            progress_callback(60)
        return selected_chunks
