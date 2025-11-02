import os
import json
import time
from bs4 import BeautifulSoup
from datetime import datetime
from groq import Groq
from tqdm import tqdm

# === CONFIG ===
MODEL = "mixtral-8x7b-32768"  # model Groq yang aktif & kuat
RAW_DIR = "data_raw"
CLEAN_DIR = "data_clean"

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_clean_text(file_path):
    """Ambil teks bersih dari file HTML."""
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")

    for tag in soup(["script", "style", "meta", "link", "noscript"]):
        tag.decompose()

    text = soup.get_text("\n", strip=True)
    lines = [line for line in text.splitlines() if len(line.strip()) > 2]
    return "\n".join(lines[:4000])  # batasi panjang teks

def parse_with_groq(text, source_name):
    """Parsing teks ke JSON menggunakan Groq API."""
    prompt = f"""
Ubah teks berikut menjadi JSON berisi informasi artis dan lagu.

Format JSON yang diharapkan:
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
      "sumber": "{source_name}"
    }}
  ]
}}

Jika tidak ditemukan, biarkan string kosong. 
Jangan tambahkan penjelasan — hanya JSON valid.
---
{text}
---
"""
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "Kamu parser teks lagu dan metadata artis. Keluarkan hanya JSON valid."},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()

def process_file(file_path):
    """Proses 1 file HTML → JSON."""
    fname = os.path.basename(file_path)
    text = extract_clean_text(file_path)

    try:
        result = parse_with_groq(text, fname)
        try:
            data = json.loads(result)
        except json.JSONDecodeError:
            print(f"⚠️ Hasil Groq tidak valid JSON di {fname} — disimpan mentah.")
            data = {"raw_output": result}
    except Exception as e:
        print(f"❌ Gagal parsing {fname}: {e}")
        data = {"artist": {}, "songs": []}

    data["updated_at"] = f"{datetime.utcnow().isoformat()}Z"
    return data

if __name__ == "__main__":
    os.makedirs(CLEAN_DIR, exist_ok=True)
    files = [f for f in os.listdir(RAW_DIR) if f.endswith(".html")]

    if not files:
        print("⚠️ Tidak ada file .html di folder data_raw/")
        exit(0)

    print(f"📂 Ditemukan {len(files)} file HTML untuk diproses.\n")

    start_time = time.time()

    for fname in tqdm(files, desc="🔄 Memproses file HTML", unit="file"):
        fpath = os.path.join(RAW_DIR, fname)
        data = process_file(fpath)

        output_path = os.path.join(
            CLEAN_DIR,
            os.path.splitext(fname)[0] + ".json"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        time.sleep(1)  # kasih jeda aman antar request (biar gak rate limit)

    elapsed = time.time() - start_time
    print(f"\n🎉 Semua file selesai dalam {elapsed:.1f} detik!")
    print(f"📁 Hasil tersimpan di folder: {CLEAN_DIR}/")