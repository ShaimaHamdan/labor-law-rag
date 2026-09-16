import requests
from bs4 import BeautifulSoup
import re

# --- CONFIG ---
SERIAL = "Sik_bO0vk9xapYfceshx6A"  # replace with the statute you want
API_URL = "https://laws-gateway.moj.gov.sa/apis/legislations/v1/statute/get-Statute-gateway-Detail"
OUTPUT_FILE = "statute_full_clean26.txt"

# --- FETCH DATA WITH HEADERS ---
headers = {"User-Agent": "Mozilla/5.0"}
params = {
    "Serial": SERIAL,
    "identityNumber": ""
}

resp = requests.get(API_URL, params=params, headers=headers, timeout=10)
resp.raise_for_status()
data = resp.json()

# --- HELPER FUNCTION TO CLEAN HTML AND RECURSE ---
def extract_text(item):
    result = []
    if "sequence" in item and item["sequence"]:
        result.append(item["sequence"])
    if "name" in item and item["name"]:
        result.append(item["name"])
    if "text" in item and item["text"]:
        clean = BeautifulSoup(item["text"], "html.parser").get_text(separator="\n").strip()
        result.append(clean)
    for sub in item.get("items") or []:
        if sub:
            result.extend(extract_text(sub))
    return result

# --- CLEAN FORMATTING FUNCTION ---
def clean_statute_text(text):
    # Collapse multiple blank lines
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    # Strip spaces at start/end of lines
    text = "\n".join(line.strip() for line in text.splitlines())
    # Normalize Arabic numbering bullets (١. → ١))
    text = re.sub(r'([١٢٣٤٥٦٧٨٩٠])\.', r'\1)', text)
    # Collapse multiple spaces
    text = re.sub(r'[ \t]+', ' ', text)
    # Remove spaces before punctuation
    text = re.sub(r'\s+([:،؛؟])', r'\1', text)
    return text

# --- EXTRACT ALL TEXT ---
statute_structure = data.get("model", {}).get("statuteStructure", [])
if not statute_structure:
    print("No content found! Check Serial or API access.")
    exit()

all_text = []
for section in statute_structure:
    all_text.extend(extract_text(section))

# --- JOIN AND CLEAN ---
plain_text = "\n\n".join(all_text)
cleaned_text = clean_statute_text(plain_text)

# --- SAVE TO FILE ---
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(cleaned_text)

print(f"Done! Full statute text saved to {OUTPUT_FILE}")
