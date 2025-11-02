import os, sys, json, glob

# ===== FIX IMPORT PATH (universal) =====
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# =======================================

from scripts.utils.text_tools import extract_lyrics_info
from scripts.utils.schema import build_song_json

RAW_DIR = "data_raw"
OUTPUT_DIR = "data_clean"
TEMP_OUTPUT = os.path.join(OUTPUT_DIR, "temp_parsed.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_files():
    all_data = []
    files = glob.glob(os.path.join(RAW_DIR, "*"))
    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            song_info = extract_lyrics_info(text, os.path.basename(fpath))
            song_json = build_song_json(song_info)
            all_data.append(song_json)
            print(f"✅ Parsed: {os.path.basename(fpath)}")

        except Exception as e:
            print(f"❌ Error parsing {fpath}: {e}")

    with open(TEMP_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"💾 Saved temp parsed JSON → {TEMP_OUTPUT}")
    return all_data

if __name__ == "__main__":
    parse_files()