import os
import re
import json
from bs4 import BeautifulSoup

INPUT_DIR = "data_raw"
OUTPUT_DIR = "data_clean"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_html(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n").strip()
    text = re.sub(r'\n+', '\n', text)
    return text

def split_by_artist(text):
    """Pisahkan teks per artis berdasarkan pola 'Lirik Lagu [ARTIST]'"""
    pattern = r"Lirik Lagu\s+([A-Za-z0-9&'\" ]+)"
    parts = re.split(pattern, text)
    chunks = []
    for i in range(1, len(parts), 2):
        artist = parts[i].strip().replace('"', '')
        content = parts[i + 1].strip()
        chunks.append((artist, content))
    return chunks

def split_by_song(text):
    """Pisahkan per lagu (berdasarkan tanda kutip atau header lagu)"""
    pattern = r"Lagu\s+([A-Za-z0-9&'\" ]+)\s+\"([^\"]+)\""
    parts = re.split(pattern, text)
    chunks = []
    for i in range(1, len(parts), 3):
        artist_ref = parts[i].strip()
        song_title = parts[i + 1].strip()
        content = parts[i + 2].strip()
        chunks.append((song_title, content))
    return chunks if chunks else [("Unknown Song", text)]

def extract_lyrics_sections(text):
    sections = {"kanji": "", "romaji": "", "terjemahan": ""}
    current = None
    for line in text.splitlines():
        l = line.strip().lower()
        if "kanji" in l:
            current = "kanji"
            continue
        elif "romaji" in l:
            current = "romaji"
            continue
        elif "indonesia" in l or "terjemahan" in l:
            current = "terjemahan"
            continue
        if current:
            sections[current] += line + "\n"
    return sections

def make_artist_profile(name):
    return {
        "Nama lengkap & nama panggung": name,
        "Asal / domisili": "",
        "Tanggal lahir": "",
        "Genre musik": "",
        "Influences / inspirasi": "",
        "Cerita perjalanan musik": "",
        "Foto profil": "",
        "Link media sosial": {
            "BandLab": "",
            "YouTube": "",
            "Spotify": "",
            "Instagram": ""
        }
    }

def parse_artist_block(artist, text):
    lagu_list = []
    songs = split_by_song(text)
    for song_title, song_text in songs:
        sections = extract_lyrics_sections(song_text)
        tanggal = re.search(r"dirilis(?: pada)? ([0-9]{1,2} [A-Za-z]+ [0-9]{4})", song_text)
        tanggal_rilis = tanggal.group(1) if tanggal else ""
        durasi = re.search(r"(\d:\d{2})", song_text)
        durasi_str = durasi.group(1) if durasi else ""
        label = ""
        if "Virgin Music" in song_text:
            label = "Virgin Music"
        elif "Sony" in song_text:
            label = "Sony Music"

        lagu_list.append({
            "Judul lagu": song_title,
            "Composer": "",
            "Lyricist": "",
            "Featuring": "",
            "Tahun rilis": tanggal_rilis[-4:] if tanggal_rilis else "",
            "Album asal": "",
            "Durasi": durasi_str,
            "Genre": "",
            "Key": "",
            "Chord & lyrics": sections["kanji"].strip(),
            "Terjemahan": sections["terjemahan"].strip()
        })

    return {
        "Bio / Profil": make_artist_profile(artist),
        "Diskografi": [{
            "Nama album/single": "",
            "Tanggal rilis": "",
            "Label": "",
            "Jumlah lagu": str(len(lagu_list)),
            "Cover art": "",
            "Produksi oleh / kolaborator tetap": "",
            "Lagu / Song List": lagu_list
        }]
    }

# === MAIN ===
for file_name in os.listdir(INPUT_DIR):
    if not file_name.endswith(".html"):
        continue

    with open(os.path.join(INPUT_DIR, file_name), "r", encoding="utf-8") as f:
        html = f.read()

    clean_text = clean_html(html)
    artist_blocks = split_by_artist(clean_text)

    for artist, block in artist_blocks:
        print(f"🎤 Memproses artis: {artist}")
        data = parse_artist_block(artist, block)
        output_file = os.path.join(OUTPUT_DIR, f"{artist}.json")

        with open(output_file, "w", encoding="utf-8") as out:
            json.dump({
                "raw_text": block,
                "parsed_info": data
            }, out, ensure_ascii=False, indent=2)

        print(f"✅ Disimpan ke {output_file}")
