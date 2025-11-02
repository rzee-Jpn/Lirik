import os, json, glob
from scripts.utils.text_tools import extract_lyrics_info

RAW_PATH = "raw_data"
TEMP_JSON = "clean_data/temp_parsed.json"

def main():
    data = []
    for file in glob.glob(os.path.join(RAW_PATH, "*")):
        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        parsed = extract_lyrics_info(text, os.path.basename(file))
        data.append(parsed)

    os.makedirs(os.path.dirname(TEMP_JSON), exist_ok=True)
    with open(TEMP_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ Parsed {len(data)} files into {TEMP_JSON}")

if __name__ == "__main__":
    main()