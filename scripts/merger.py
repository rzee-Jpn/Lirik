import os, sys, json

# ===== FIX IMPORT PATH =====
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
# ===========================

OUTPUT_DIR = "data_clean"
FINAL_JSON = os.path.join(OUTPUT_DIR, "songs_merged.json")
TEMP_PARSED = os.path.join(OUTPUT_DIR, "temp_parsed.json")

def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def smart_merge(old_data, new_data):
    merged = {d["judul_lagu"].lower(): d for d in old_data}

    for song in new_data:
        key = song["judul_lagu"].lower()
        if key in merged:
            # update field tanpa hapus data lama
            for k, v in song.items():
                if v and (v != merged[key].get(k)):
                    merged[key][k] = v
        else:
            merged[key] = song

    return list(merged.values())

def merge_all():
    old = load_json(FINAL_JSON)
    new = load_json(TEMP_PARSED)
    merged = smart_merge(old, new)

    with open(FINAL_JSON, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"✅ Merged {len(new)} songs → total {len(merged)} saved to {FINAL_JSON}")

if __name__ == "__main__":
    merge_all()