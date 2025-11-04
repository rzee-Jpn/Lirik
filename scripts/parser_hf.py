import os
import re
import json
from transformers import pipeline

# ==============================
# ⚙️ Konfigurasi
# ==============================
MODEL_NAME = "google/flan-t5-base"
INPUT_DIR = "data_raw"
OUTPUT_DIR = "data_clean"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==============================
# 🔧 Load Model
# ==============================
print("🔄 Memuat model HuggingFace...")
nlp = pipeline("text2text-generation", model=MODEL_NAME)
print("✅ Model siap digunakan!")

# ==============================
# 🧠 Fungsi bantu
# ==============================
def extract_json(text):
    """Ambil JSON valid dari teks model"""
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print("⚠️ JSON tidak valid:", e)
    return {"raw_output": text}


def split_artists(text):
    """
    Deteksi multi-artis dalam satu teks.
    Berdasarkan pola umum seperti 'Lirik Lagu [Nama Artis]'
    """
    pattern = r"(?:Lirik\s+Lagu|Lagu)\s+([A-Z][A-Za-z0-9 _'\-]+)"
    artists = re.findall(pattern, text)
    if not artists:
        artists = ["Unknown"]
    parts = re.split(pattern, text)
    result = []
    for i, artist in enumerate(artists):
        content = parts[i + 1] if i + 1 < len(parts) else text
        result.append((artist.strip(), content.strip()))
    return result


# ==============================
# 🚀 Jalankan Parsing
# ==============================
for file_name in os.listdir(INPUT_DIR):
    if not file_name.endswith(".html"):
        continue

    print(f"📝 Memproses: {file_name}")
    with open(os.path.join(INPUT_DIR, file_name), "r", encoding="utf-8") as f:
        text = f.read()

    # Deteksi artis ganda
    artist_blocks = split_artists(text)

    for artist_name, artist_text in artist_blocks:
        print(f"🎤 Memproses artis: {artist_name}")

        prompt = f"""
        Dari teks berikut, susun informasi artis musik dan karyanya secara rapi dalam JSON.
        Gunakan struktur berikut dan isi sebisa mungkin berdasarkan konteks teks:

        {{
          "Bio / Profil": {{
            "Nama lengkap": "",
            "Nama panggung": "{artist_name}",
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

        Teks:
        {artist_text}
        """

        # Jalankan model
        result = nlp(prompt, max_new_tokens=2048)[0]["generated_text"]

        # Ambil JSON valid
        parsed = extract_json(result)

        # Simpan hasil ke file terpisah
        safe_name = re.sub(r"[^\w\-_ ]", "_", artist_name)
        out_path = os.path.join(OUTPUT_DIR, f"{safe_name}.json")
        with open(out_path, "w", encoding="utf-8") as out_file:
            json.dump({
                "raw_text": artist_text,
                "parsed_info": parsed
            }, out_file, ensure_ascii=False, indent=2)

        print(f"✅ Hasil disimpan ke {safe_name}.json")

print("🎉 Semua artis & file selesai diproses!")