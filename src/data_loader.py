import json
from pathlib import Path


def load_jsonl(file_path: Path):
    with file_path.open("r", encoding="utf-8") as file:
        return [json.loads(line) for line in file]


class JsonlDataLoader:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._data = None

    def load(self):
        if self._data is None:
            self._data = load_jsonl(self.file_path)
        return self._data
