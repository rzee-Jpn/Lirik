import os
import json
from bs4 import BeautifulSoup
from transformers import pipeline

# ✅ Model publik gratis (tidak perlu API key)
MODEL_NAME = "google/flan-t5-small"

# Siapkan pipeline Hugging Face
nlp = pipeline("text2text-generation", model=MODEL_NAME)

# Folder input/output
INPUT_FOLDER = "data_raw"
OUTPUT_FOLDER = "data_clean"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Fungsi untuk ekstrak teks dari HTML
def extract_text_from_html(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    return soup.get_text(separator="\n", strip=True)

# Fungsi untuk memanggil model HF dengan batching otomatis
def generate_response(prompt, max_length=512):
    try:
        result = nlp(prompt, max_length=max_length, truncation=True)
        return result[0]['generated_text']
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return ""

# Proses setiap file HTML
for file_name in os.listdir(INPUT_FOLDER):
    if not file_name.endswith(".html"):
        continue

    print(f"🎵 Processing {file_name}...")
    text = extract_text_from_html(os.path.join(INPUT_FOLDER, file_name))

    # Bagi teks panjang agar tidak error
    chunk_size = 1500
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    # Gabungkan hasil parsing tiap bagian
    artist_info = []
    for i, chunk in enumerate(chunks, 1):
        print(f"🧩 Parsing bagian {i}/{len(chunks)}...")
        prompt = f"""
        Ekstrak dan susun informasi dari teks berikut dalam format JSON terstruktur:
        ---
        {chunk}
        ---
        Format hasil JSON yang diharapkan:

        {{
          "Bio / Profil": {{
            "Nama lengkap": "",
            "Nama panggung": "",
            "Asal / domisili": "",
            "Tanggal lahir": "",
            "Genre musik": "",
            "Influences / inspirasi": "",
            "Cerita perjalanan musik": "",
            "Foto profil": "",
            "Link media sosial": {{
              "BandLab": "",
              "YouTube": "",
              "Spotify": "",
              "Instagram": ""
            }}
          }},
          "Diskografi": [
            {{
              "Nama album/single": "",
              "Tanggal rilis": "",
              "Label": "",
              "Jumlah lagu": "",
              "Cover art": "",
              "Produksi oleh": "",
              "Lagu": [
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
                  "Chord & lyrics": "",
                  "Terjemahan": ""
                }}
              ]
            }}
          ]
        }}
        """

        parsed = generate_response(prompt)
        if parsed:
            artist_info.append(parsed)

    # Gabungkan semua hasil bagian
    combined_output = "\n".join(artist_info)

    # Simpan hasil JSON
    out_path = os.path.join(OUTPUT_FOLDER, file_name.replace(".html", ".json"))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"raw_text": text, "parsed_info": combined_output}, f, ensure_ascii=False, indent=2)

    print(f"✅ Hasil disimpan ke {out_path}\n")