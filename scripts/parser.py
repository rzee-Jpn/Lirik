# parser.py
import os, re, json
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

DATA_RAW = Path("data_raw")
ARTISTS_DIR = Path("artists")
ARTISTS_DIR.mkdir(exist_ok=True)

def extract_chord_lyrics_from_html(html_text):
    """Ambil lirik + chord dari elemen <pre> atau <div>."""
    soup = BeautifulSoup(html_text, "html.parser")
    pre = soup.find("pre") or soup.find("div", class_="lyrics")
    if not pre:
        return None, None, []

    lines = pre.get_text("\n").splitlines()
    combined = []
    chords_used = set()

    for line in lines:
        # deteksi baris yang punya chord (huruf besar & spasi)
        chord_line = re.findall(r"\b[A-G][#bm\d/]*\b", line)
        if chord_line:
            chords_used.update(chord_line)
            combined.append({"chord": " ".join(chord_line), "line": ""})
        else:
            if combined and combined[-1]["line"] == "":
                combined[-1]["line"] = line.strip()
            else:
                combined.append({"chord": "", "line": line.strip()})

    lyrics_plain = "\n".join(l["line"] for l in combined if l["line"])
    return lyrics_plain, combined, list(chords_used)

def parse_artist_folder(artist_folder):
    artist_name = artist_folder.name
    artist_data = {
        "artist": artist_name.title(),
        "biography": "",
        "extra_info": {},
        "albums": [],
        "singles": []
    }

    for file in artist_folder.iterdir():
        ext = file.suffix.lower()
        fname = file.stem.lower()

        if ext in [".html", ".htm"]:
            html_text = file.read_text(encoding="utf-8", errors="ignore")
            if "bio" in fname:
                # file biografi
                artist_data["biography"] = BeautifulSoup(html_text, "html.parser").get_text(" ").strip()
            else:
                # anggap file lagu
                lyrics_plain, lyrics_chord, chords_used = extract_chord_lyrics_from_html(html_text)
                song_obj = {
                    "title": fname.replace("_", " ").title(),
                    "lyrics_plain": lyrics_plain,
                    "lyrics_chord": lyrics_chord,
                    "chords_used": chords_used,
                    "metadata": {
                        "source": str(file),
                        "fetched_at": datetime.utcnow().isoformat() + "Z"
                    }
                }
                if "album" in fname:
                    album_title = re.sub(r"album[_-]?", "", fname).title()
                    artist_data["albums"].append({"title": album_title, "year": "", "songs": [song_obj]})
                elif "single" in fname:
                    artist_data["singles"].append(song_obj)
                else:
                    # lagu lepas
                    artist_data["singles"].append(song_obj)

        elif ext == ".json":
            try:
                extra_info = json.load(open(file, encoding="utf-8"))
                artist_data["extra_info"].update(extra_info)
            except Exception as e:
                print(f"⚠️ Error parsing {file}: {e}")

    return artist_data

def main():
    for artist_folder in DATA_RAW.iterdir():
        if artist_folder.is_dir():
            artist_json = parse_artist_folder(artist_folder)
            out_path = ARTISTS_DIR / f"{artist_folder.name.lower().replace(' ', '-')}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(artist_json, f, ensure_ascii=False, indent=2)
            print(f"✅ Saved: {out_path}")

if __name__ == "__main__":
    main()