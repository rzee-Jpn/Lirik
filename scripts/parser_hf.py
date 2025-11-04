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

def extract_lyrics_sections(text):
    """Pisahkan bagian Kanji, Romaji, dan Terjemahan"""
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
    """Template bio per artis, bisa kamu perluas nanti"""
    default_bio = {
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
    bio = {"Nama lengkap & nama panggung": name}
    bio.update(default_bio)
    return bio

def parse_html_for_artist(artist_name, text):
    sections = extract_lyrics_sections(text)

    # deteksi nama lagu utama dari teks (jika ada)
    match = re.search(r'"([^"]+)"', text)
    title_guess = match.group(1) if match else "Unknown Song"

    diskografi = [{
        "Nama album/single": "",
        "Tanggal rilis": "",
        "Label": "",
        "Jumlah lagu": "",
        "Cover art": "",
        "Produksi oleh / kolaborator tetap": "",
        "Lagu / Song List": [{
            "Judul lagu": title_guess,
            "Composer": "",
            "Lyricist": "",
            "Featuring": "",
            "Tahun rilis": "",
            "Album asal": "",
            "Durasi": "",
            "Genre": "",
            "Key": "",
            "Chord & lyrics": sections["kanji"].strip(),
            "Terjemahan": sections["terjemahan"].strip()
        }]
    }]

    return {
        "Bio / Profil": make_artist_profile(artist_name),
        "Diskografi": diskografi
    }

# === MAIN PROCESS ===
for file_name in os.listdir(INPUT_DIR):
    if not file_name.endswith(".html"):
        continue

    artist_name = os.path.splitext(file_name)[0]  # ambil nama artis dari nama file
    input_path = os.path.join(INPUT_DIR, file_name)
    output_path = os.path.join(OUTPUT_DIR, f"{artist_name}.json")

    print(f"🔍 Memproses {artist_name}...")

    with open(input_path, "r", encoding="utf-8") as f:
        html = f.read()

    clean_text = clean_html(html)
    structured = parse_html_for_artist(artist_name, clean_text)

    with open(output_path, "w", encoding="utf-8") as out:
        json.dump({
            "raw_text": clean_text,
            "parsed_info": structured
        }, out, ensure_ascii=False, indent=2)

    print(f"✅ Disimpan: {output_path}")