import faiss
import numpy as np
import os
import shutil
import tempfile


class FaissVectorStore:
    def __init__(self, index_file):
        self.index_file = index_file
        self._index = None

    def save(self, vectors):
        vectors = np.array(vectors).astype("float32")
        if vectors.ndim != 2 or not vectors.shape[0] or not vectors.shape[1]:
            raise ValueError("Cannot build a FAISS index without embedding vectors.")
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)

        temporary_path = self._temporary_path()
        try:
            faiss.write_index(index, temporary_path)
            shutil.copyfile(temporary_path, self.index_file)
        finally:
            self._remove_temporary_path(temporary_path)

    def search(self, vector, k: int):
        if vector.ndim != 2 or not vector.shape[0] or not vector.shape[1]:
            raise ValueError("Cannot search FAISS with an empty query vector.")

        if self._index is None:
            if not self.index_file.exists():
                raise FileNotFoundError(
                    f"FAISS index not found: {self.index_file}. "
                    "Run build_faiss.py first."
                )

            temporary_path = self._temporary_path()
            try:
                shutil.copyfile(self.index_file, temporary_path)
                self._index = faiss.read_index(temporary_path)
            finally:
                self._remove_temporary_path(temporary_path)

        return self._index.search(vector, k)

    @staticmethod
    def _temporary_path():
        descriptor, path = tempfile.mkstemp(suffix=".bin")
        os.close(descriptor)
        return path

    @staticmethod
    def _remove_temporary_path(path):
        try:
            os.remove(path)
        except FileNotFoundError:
            pass
