import json, os
from scripts.utils.schema import base_song_template

MAIN_JSON = "clean_data/songs.json"
TEMP_JSON = "clean_data/temp_parsed.json"

def merge_data():
    if not os.path.exists(TEMP_JSON):
        print("⚠️ No temp data to merge.")
        return

    existing = []
    if os.path.exists(MAIN_JSON):
        with open(MAIN_JSON, "r", encoding="utf-8") as f:
            existing = json.load(f)

    with open(TEMP_JSON, "r", encoding="utf-8") as f:
        new_data = json.load(f)

    merged = {song["unique_id"]: song for song in existing}
    for song in new_data:
        uid = song["unique_id"]
        if uid not in merged:
            merged[uid] = song
        else:
            # hanya tambahkan field baru tanpa hapus data lama
            for key, val in song.items():
                if val and key not in merged[uid]:
                    merged[uid][key] = val

    final = list(merged.values())
    with open(MAIN_JSON, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f"✅ Merged {len(new_data)} new entries → {len(final)} total songs")

if __name__ == "__main__":
    merge_data()