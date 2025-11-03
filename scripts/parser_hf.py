import os
import json
import re
from bs4 import BeautifulSoup
from transformers import pipeline

INPUT_FOLDER = "data_raw"
OUTPUT_FOLDER = "data_clean"

# Ganti model dengan model HuggingFace yang kamu pakai
MODEL_NAME = "meta-llama/Meta-Llama-3-8B-Instruct"
nlp = pipeline("text-generation", model=MODEL_NAME)

def clean_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator="\n")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def parse_with_ai(text):
    prompt = f"""
    Kamu adalah AI yang mengekstrak informasi musik dari teks.
    Buat JSON dengan format berikut:

    {{
      "Bio / Profil": {{
        "Nama lengkap": "",
        "Nama panggung": "",
        "Asal / Domisili": "",
        "Tanggal lahir": "",
        "Genre musik": [],
        "Influences / Inspirasi": [],
        "Cerita perjalanan musik": "",
        "Foto profil": "",
        "Link media sosial": {{
          "BandLab": "",
          "YouTube": "",
          "Spotify": "",
          "Instagram": ""
        }}
      }},
      "Diskografi (Album / Single)": [
        {{
          "Nama album/single": "",
          "Tanggal rilis": "",
          "Label / Independent": "",
          "Jumlah lagu": "",
          "Cover art": "",
          "Produksi oleh / Kolaborator tetap": [],
          "Lagu / Song List": [
            {{
              "Judul lagu": "",
              "Composer": "",
              "Lyricist": "",
              "Featuring": "",
              "Tahun rilis": "",
              "Album asal": "",
              "Durasi": "",
              "Genre": "",
              "Key": "",
              "Chord & Lyrics": "",
              "Terjemahan": ""
            }}
          ]
        }}
      ]
    }}

    Hasilkan hanya JSON valid tanpa penjelasan tambahan.
    Teks sumber:
    {text}
    """
    result = nlp(prompt, max_length=1024, truncation=True)
    raw_output = result[0]["generated_text"]

    try:
        parsed = json.loads(raw_output)
    except Exception:
        parsed = {"raw_text": text, "parsed_output": raw_output}
    return parsed

def save_json(artist, data):
    artist_folder = os.path.join(OUTPUT_FOLDER, artist)
    os.makedirs(artist_folder, exist_ok=True)
    with open(os.path.join(artist_folder, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    for file_name in os.listdir(INPUT_FOLDER):
        if file_name.endswith(".html"):
            with open(os.path.join(INPUT_FOLDER, file_name), "r", encoding="utf-8") as f:
                html_content = f.read()
            clean_text = clean_html(html_content)
            result = parse_with_ai(clean_text)

            artist = result.get("Bio / Profil", {}).get("Nama panggung", "Unknown").replace(" ", "_")
            save_json(artist, result)
            print(f"✅ Parsed & saved: {artist}")

if __name__ == "__main__":
    main()