import os
import json
from bs4 import BeautifulSoup
from datetime import datetime
from groq import Groq
import textwrap

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

def extract_text_from_html(file_path):
    """Ambil teks dari HTML (hapus tag, ambil konten utama)."""
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    text = soup.get_text(separator="\n", strip=True)
    return text

def chunk_text(text, max_len=6000):
    """Pisahkan teks jadi beberapa bagian agar tidak melebihi context limit."""
    return textwrap.wrap(text, max_len, break_long_words=False, replace_whitespace=False)

def parse_chunk_with_groq(chunk_text):
    """Gunakan Groq untuk parsing 1 bagian HTML jadi JSON parsial."""
    prompt = f"""
Kamu adalah parser HTML yang mengekstrak data lirik dan artis dari teks.
Berikan hasil JSON parsial (boleh 1 lagu saja per chunk) dalam format ini:

{{
  "artist": {{
    "nama_asli": "",
    "nama_panggung": "",
    "tanggal_lahir": "",
    "asal": "",
    "media_sosial": {{
      "instagram": "",
      "x": "",
      "tiktok": "",
      "youtube": ""
    }},
    "label": "",
    "pembuat_lirik": "",
    "komposer": "",
    "aransemen": "",
    "produser": ""
  }},
  "songs": [
    {{
      "judul_lagu": "",
      "album": "",
      "tahun_rilis": "",
      "genre": "",
      "lirik_dengan_chord": "",
      "sumber": "lirik.html"
    }}
  ]
}}

Jika tidak ada data, tetap kirim struktur kosong dengan string kosong.
Teks input:
---
{chunk_text}
---
"""

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Kamu menghasilkan JSON artis dan lagu dari HTML."},
            {"role": "user", "content": prompt}
        ],
    )
    return resp.choices[0].message.content

def safe_json_parse(text):
    """Coba parse string ke JSON, kembalikan dict kosong jika gagal."""
    try:
        return json.loads(text)
    except Exception:
        return {}

if __name__ == "__main__":
    data_raw_path = "data_raw/lirik.html"
    output_path = "data_clean/lirik_parsed.json"

    print("🔍 Parsing lirik.html...")

    if not os.path.exists(data_raw_path):
        print("⚠️ File data_raw/lirik.html tidak ditemukan.")
        exit(1)

    html_text = extract_text_from_html(data_raw_path)
    chunks = chunk_text(html_text, max_len=6000)

    all_songs = []
    artist_info = {}
    print(f"📄 File dibagi jadi {len(chunks)} bagian...")

    for i, chunk in enumerate(chunks, 1):
        print(f"🧩 Parsing bagian {i}/{len(chunks)}...")
        try:
            result_str = parse_chunk_with_groq(chunk)
            result_json = safe_json_parse(result_str)

            # Ambil data artis (jika ada)
            if "artist" in result_json and not artist_info:
                artist_info = result_json["artist"]

            # Gabung semua lagu
            if "songs" in result_json:
                all_songs.extend(result_json["songs"])

        except Exception as e:
            print(f"⚠️ Gagal parsing chunk {i}: {e}")

    # Buat JSON akhir
    final_data = {
        "artist": artist_info,
        "updated_at": f"{datetime.utcnow().isoformat()}Z",
        "songs": all_songs
    }

    os.makedirs("data_clean", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Parsing selesai! Disimpan ke: {output_path}")