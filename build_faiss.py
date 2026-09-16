
# build_faiss.py
# Builds FAISS index using Qwen embeddings + your chunks.jsonl

from tqdm import tqdm
import json

from src.config import Settings
from src.data_loader import JsonlDataLoader
from src.embedding import OllamaEmbedding
from src.vector_store import FaissVectorStore


SETTINGS = Settings.from_root()
CHUNKS_FILE = SETTINGS.chunks_file
INDEX_FILE = SETTINGS.index_file
META_FILE = SETTINGS.metadata_file
embedder = OllamaEmbedding(SETTINGS.embedding_model, SETTINGS.ollama_host)

# ----------------------------
# Ollama client
# ----------------------------
def load_chunks():
    return JsonlDataLoader(CHUNKS_FILE).load()


# ----------------------------
# Get embeddings in batches
# ----------------------------
def embed_batch(batch_texts):
    return embedder.embed_batch(batch_texts)


# ----------------------------
# Main build
# ----------------------------
def main():

    chunks = load_chunks()

    print(f"Loaded {len(chunks)} chunks")

    vectors = []
    metadata = []

    BATCH = 50

    texts = [c["text"] for c in chunks]

    # ----------------------------
    # Generate embeddings
    # ----------------------------
    for i in tqdm(range(0, len(texts), BATCH)):

        batch = texts[i:i + BATCH]

        embeds = embed_batch(batch)

        vectors.extend(embeds)

        # Matching metadata
        for c in chunks[i:i + BATCH]:
            metadata.append(c)

    # ----------------------------
    # Convert to numpy
    # ----------------------------
    print(f"Embedding shape: ({len(vectors)}, {len(vectors[0])})")

    # ----------------------------
    # Build FAISS index
    # ----------------------------
    FaissVectorStore(INDEX_FILE).save(vectors)

    print(f"Saved FAISS index → {INDEX_FILE}")

    # ----------------------------
    # Save metadata
    # ----------------------------
    with open(META_FILE, "w", encoding="utf-8") as f:

        for m in metadata:
            f.write(
                json.dumps(
                    m,
                    ensure_ascii=False
                ) + "\n"
            )

    print(f"Saved metadata → {META_FILE}")

    print("Done.")


if __name__ == "__main__":
    main()

