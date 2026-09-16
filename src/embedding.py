import numpy as np
from ollama import Client


class OllamaEmbedding:
    def __init__(self, model: str, host: str):
        self.model = model
        self.client = Client(host=host)

    def embed(self, text: str):
        response = self.client.embed(
            model=self.model,
            input=text,
            keep_alive="24h",
        )
        embeddings = response.get("embeddings", [])
        if not embeddings or not embeddings[0]:
            raise RuntimeError("Ollama returned no embedding. Check that the embedding model is available.")
        return embeddings[0]

    def embed_batch(self, texts):
        response = self.client.embed(
            model=self.model,
            input=texts,
            keep_alive="24h",
        )
        embeddings = response.get("embeddings", [])
        if not embeddings:
            raise RuntimeError("Ollama returned no embeddings. Check that the embedding model is available.")
        return embeddings

    @staticmethod
    def as_vector(embedding):
        return np.array([embedding]).astype("float32")
