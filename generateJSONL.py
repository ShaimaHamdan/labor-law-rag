
#!/usr/bin/env python3

import re
import json
import hashlib
from pathlib import Path


# ---------------------------------------------
# Paths
# ---------------------------------------------
INPUT_FILE = Path("segment/labor_law_articles.json")
OUTPUT_FILE = Path("chunks.jsonl")

MIN_LEN = 25


# ---------------------------------------------
# Arabic normalization
# ---------------------------------------------
def clean(text: str) -> str:
    text = text.replace("\ufeff", "")
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


# ---------------------------------------------
# SHA1
# ---------------------------------------------
def sha1(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


# ---------------------------------------------
# Main
# ---------------------------------------------
def main():

    if not INPUT_FILE.exists():
        print(f"File not found: {INPUT_FILE}")
        return

    # Load JSON
    with INPUT_FILE.open("r", encoding="utf-8") as file:
        articles = json.load(file)

    if not isinstance(articles, list):
        print("Error: JSON file must contain a list of articles.")
        return

    seen_hashes = set()
    total = 0

    with OUTPUT_FILE.open("w", encoding="utf-8") as out:

        for idx, article in enumerate(articles, start=1):

            article_name = article.get("article", "")
            text = clean(article.get("text", ""))

            if len(text) < MIN_LEN:
                continue

            # Remove duplicate articles
            h = sha1(text)

            if h in seen_hashes:
                continue

            seen_hashes.add(h)

            doc = {
                "id": f"article_{idx}",
                "source_file": INPUT_FILE.name,
                "sequence": article_name,
                "page": article.get("page"),
                "source": article.get("source"),
                "source_url": article.get("source_url"),
                "chunk_index": idx,
                "text": text
            }

            out.write(
                json.dumps(
                    doc,
                    ensure_ascii=False
                ) + "\n"
            )

            total += 1

    print(
        f"✓ Done. {total} unique مادة-chunks "
        f"saved → {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
