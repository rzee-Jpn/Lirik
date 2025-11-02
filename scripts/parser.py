import os, sys, json, glob
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from difflib import SequenceMatcher  # untuk fuzzy matching

# ===== PATH FIX =====
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.abspath(os.path.join(root_dir, "..")))
# ====================

RAW_DIR = Path("data_raw")
OUTPUT_DIR = Path("artists")
OUTPUT_DIR.mkdir(exist_ok=True)


# ==================== UTILITIES ====================
def safe_slug(name):
    return name.lower().replace(" ", "-").replace("/", "-").strip()

def load_json(path: Path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def now_iso():
    return datetime.utcnow().isoformat() + "Z"

def similarity(a, b):
    """Hitung kemiripan dua string (0.0 - 1.0)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
# ====================================================


# ====================================================
# 🧩 PARSER DASAR (HTML & TXT)
# ====================================================
def extract_lyrics_info(text: str, filename: str):
    info = {
        "judul_lagu": "",
        "artis": "",
        "album": "",
        "tahun_rilis": "",
        "lirik_dengan_chord": "",
        "sumber": filename,
    }

    # --- HTML ---
    if "<html" in text.lower():
        soup = BeautifulSoup(text, "html.parser")
        title_tag = soup.find("title")
        info["judul_lagu"] = title_tag.text.strip() if title_tag else ""
        pre = soup.find("pre")
        lyrics_block = soup.find(class_="lyrics") or pre
        if lyrics_block:
            info["lirik_dengan_chord"] = lyrics_block.get_text("\n", strip=True)
    else:
        # --- TXT ---
        lines = text.strip().splitlines()
        info["judul_lagu"] = lines[0].strip() if lines else filename
        info["lirik_dengan_chord"] = "\n".join(lines)

    # --- Deteksi artis dari nama file ---
    parts = os.path.splitext(filename)[0].split("-")
    if len(parts) >= 2:
        info["artis"] = parts[0].strip()
        if not info["judul_lagu"]:
            info["judul_lagu"] = parts[1].strip()

    return info


# ====================================================
# 🧩 MERGE PER ARTIS (SMART)
# ====================================================
def merge_song_into_artist(existing_data, new_song, threshold=0.8):
    """Tambahkan / update lagu dengan deteksi kemiripan judul."""
    if not existing_data:
        existing_data = {
            "artist": new_song.get("artis", ""),
            "updated_at": now_iso(),
            "songs": []
        }

    # cari lagu mirip
    best_match = None
    best_ratio = 0.0
    for song in existing_data["songs"]:
        ratio = similarity(song["judul_lagu"], new_song["judul_lagu"])
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = song

    if best_match and best_ratio >= threshold:
        # update lagu lama (replace fields kosong)
        for k, v in new_song.items():
            if v and not best_match.get(k):
                best_match[k] = v
        best_match["updated_at"] = now_iso()
        print(f"🧠 Updated existing: {new_song['judul_lagu']} (similar {best_ratio:.0%})")
    else:
        # tambahkan lagu baru
        existing_data["songs"].append(new_song)
        existing_data["updated_at"] = now_iso()
        print(f"✅ Added new: {new_song['judul_lagu']}")

    return existing_data


# ====================================================
# 🚀 MAIN PROCESS
# ====================================================
def parse_all_files():
    files = list(RAW_DIR.glob("*"))
    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            song_data = extract_lyrics_info(text, file_path.name)
            artist_slug = safe_slug(song_data["artis"] or "unknown")
            artist_path = OUTPUT_DIR / f"{artist_slug}.json"

            existing = load_json(artist_path)
            merged = merge_song_into_artist(existing, song_data)
            save_json(artist_path, merged)

        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")

    print("🎉 Done parsing all files!")


if __name__ == "__main__":
    parse_all_files()