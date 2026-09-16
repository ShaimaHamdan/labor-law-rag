import json
from pathlib import Path


INPUT_FILE = Path("segment/labor_law_articles.json")

MIN_LEN = 25


def main():

    if not INPUT_FILE.exists():
        print(f"File not found: {INPUT_FILE}")
        return

    # Load JSON
    with INPUT_FILE.open("r", encoding="utf-8") as f:
        articles = json.load(f)

    if not isinstance(articles, list):
        print("Error: JSON file must contain a list of articles.")
        return

    # Basic statistics
    total_articles = len(articles)

    valid_articles = 0
    short_articles = 0
    empty_articles = 0

    lengths = []

    for article in articles:

        text = article.get("text", "").strip()

        if not text:
            empty_articles += 1
            continue

        text_length = len(text)
        lengths.append(text_length)

        if text_length < MIN_LEN:
            short_articles += 1
        else:
            valid_articles += 1

    print("=" * 50)
    print("Labor Law Chunk Length Test")
    print("=" * 50)

    print(f"Input file       : {INPUT_FILE}")
    print(f"Total articles   : {total_articles}")
    print(f"Valid articles   : {valid_articles}")
    print(f"Short articles   : {short_articles}")
    print(f"Empty articles   : {empty_articles}")

    if lengths:
        print(f"Shortest text    : {min(lengths)} characters")
        print(f"Longest text     : {max(lengths)} characters")
        print(f"Average length   : {sum(lengths) / len(lengths):.2f} characters")

    print("=" * 50)


if __name__ == "__main__":
    main()