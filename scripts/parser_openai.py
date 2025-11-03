import os
import json
import datetime
import time
import textwrap
from bs4 import BeautifulSoup
from openai import OpenAI

# 🔑 Ambil API key dari environment
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY tidak ditemukan di environment.")

client = OpenAI(api_key=API_KEY)

# ✅ Model yang akan dipakai
MODEL = "gpt-4o-mini"

RAW_DIR = "data_raw"
OUT_DIR = "data_clean"
os.makedirs(OUT_DIR, exist_ok=True)

def openai_request(messages):
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=2048
        )
        return resp.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"⚠️ Request ke OpenAI gagal: {e}")

def parse_html_with_openai(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator="\n", strip=True)

    # 🔹 Potong teks panjang jadi beberapa bagian
    chunks = textwrap.wrap(text, 8000)
    all_songs = []
    artist_info = {}

    print(f"📄 File dibagi jadi {len(chunks)} bagian...")

    for i, chunk in enumerate(chunks, start=1):
        print(f"🧩 Parsing bagian {i}/{len(chunks)}...")
        prompt = f"""
Kamu parser musik. Ekstrak semua informasi artis dan lagu dari teks ini.
Hasilkan JSON valid dengan format:
{{
  "artist": {{
    "nama_asli": "",
    "nama_panggung": "",
    "tanggal_lahir": "",
    "asal": "",
    "label": "",
    "media_sosial": {{}}
  }},
  "songs": [
    {{
      "judul_lagu": "",
      "album": "",
      "tahun_rilis": "",
      "pembuat_lirik": "",
      "composer": "",
      "arranger": "",
      "aransemen": "",
      "lirik_dengan_chord": ""
    }}
  ]
}}

Teks:
{chunk}
"""
        try:
            response_text = openai_request([
                {"role": "system", "content": "Kamu parser JSON yang disiplin, hanya keluarkan JSON valid."},
                {"role": "user", "content": prompt}
            ])
            data = json.loads(response_text)
            if not artist_info and "artist" in data:
                artist_info = data["artist"]
            if "songs" in data:
                all_songs.extend(data["songs"])
        except Exception as e:
            print(f"⚠️ Bagian {i} gagal: {e}")
            continue

    return {
        "artist": artist_info,
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "songs": all_songs
    }

# 🚀 Main process
html_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".html")]
print(f"📂 Ditemukan {len(html_files)} file HTML di folder {RAW_DIR}.\n")

for file_name in html_files:
    file_path = os.path.join(RAW_DIR, file_name)
    print(f"🔄 Memproses: {file_name}")

    parsed_data = parse_html_with_openai(file_path)
    artist_name = parsed_data.get("artist", {}).get("nama_panggung", "unknown") or "unknown"
    out_file = os.path.join(OUT_DIR, f"{artist_name.replace(' ', '_').lower()}.json")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Disimpan → {out_file}\n")

print("🎉 Semua file selesai diproses!")