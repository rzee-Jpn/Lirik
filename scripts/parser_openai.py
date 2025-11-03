import os, json, datetime, textwrap
from bs4 import BeautifulSoup
import openai

# Ambil API key OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("❌ OPENAI_API_KEY tidak ditemukan.")
openai.api_key = OPENAI_API_KEY

RAW_DIR = "data_raw"
OUT_DIR = "data_clean"
os.makedirs(OUT_DIR, exist_ok=True)

def chunk_text(text, size=8000):
    return textwrap.wrap(text, size)

def parse_chunk(chunk):
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
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # Bisa ganti dengan gpt-4o atau gpt-3.5-turbo
        messages=[
            {"role": "system", "content": "Kamu parser JSON disiplin."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=2048
    )
    return response.choices[0].message.content

def parse_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator="\n", strip=True)

    chunks = chunk_text(text)
    all_songs = []
    artist_info = {}

    for i, chunk in enumerate(chunks, start=1):
        print(f"🧩 Parsing bagian {i}/{len(chunks)}...")
        try:
            parsed_text = parse_chunk(chunk)
            data = json.loads(parsed_text)
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

def main():
    html_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".html")]
    for file_name in html_files:
        file_path = os.path.join(RAW_DIR, file_name)
        print(f"🔄 Memproses: {file_name}")
        parsed_data = parse_html_file(file_path)

        artist_name = parsed_data.get("artist", {}).get("nama_panggung", "unknown") or "unknown"
        out_file = os.path.join(OUT_DIR, f"{artist_name.replace(' ', '_').lower()}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Disimpan → {out_file}")

if __name__ == "__main__":
    main()
