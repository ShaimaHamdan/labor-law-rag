from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    chunks_file: Path
    index_file: Path
    metadata_file: Path
    embedding_model: str = "qwen3-embedding:0.6b"
    llm_model: str = "qwen3:8b"
    ollama_host: str = "http://localhost:11434"
    top_k: int = 5
    candidate_k: int = 15
    max_output_tokens: int = 384
    cache_size: int = 32

    @classmethod
    def from_root(cls, project_root: Path | None = None):
        root = (project_root or Path(__file__).resolve().parent.parent).resolve()
        return cls(
            project_root=root,
            chunks_file=root / "chunks.jsonl",
            index_file=root / "faiss_index.bin",
            metadata_file=root / "metadata.jsonl",
        )
