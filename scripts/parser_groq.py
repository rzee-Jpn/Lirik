import os, json, datetime, time, textwrap
from bs4 import BeautifulSoup
from groq import Groq

# 🔑 Ambil API key
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY tidak ditemukan di environment.")
client = Groq(api_key=API_KEY)

# ✅ Model baru Groq yang aktif per November 2025
MODEL_CANDIDATES = [
    "llama-3.2-90b-text-preview",
    "llama-3.2-11b-text-preview",
]

RAW_DIR = "data_raw"
OUT_DIR = "data_clean"
os.makedirs(OUT_DIR, exist_ok=True)

def groq_request(messages):
    for model in MODEL_CANDIDATES:
        try:
            print(f"🧠 Coba model: {model}")
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=2048,
            )
            print(f"✅ Sukses pakai model: {model}")
            return resp.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Model {model} gagal: {e}")
            time.sleep(2)
    raise RuntimeError("❌ Semua model gagal dipakai.")

def parse_html_with_groq(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator="\n", strip=True)

    # 🔹 Potong teks panjang jadi beberapa bagian agar tidak kena limit
    chunks = textwrap.wrap(text, 8000)  # 8K karakter per batch
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
            response_text = groq_request([
                {"role": "system", "content": "Kamu adalah parser JSON yang disiplin dan hanya keluarkan JSON valid."},
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
print("📂 Mendeteksi file HTML di folder:", RAW_DIR)
html_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".html")]
print(f"🔍 Ditemukan {len(html_files)} file HTML untuk diproses.\n")

for file_name in html_files:
    file_path = os.path.join(RAW_DIR, file_name)
    print(f"🔄 Memproses: {file_name}")

    parsed_data = parse_html_with_groq(file_path)
    if parsed_data:
        artist_name = parsed_data.get("artist", {}).get("nama_panggung", "unknown") or "unknown"
        out_file = os.path.join(OUT_DIR, f"{artist_name.replace(' ', '_').lower()}.json")
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)
        print(f"✅ Disimpan → {out_file}\n")
    else:
        print(f"⚠️ Gagal memproses file {file_name}\n")

print("🎉 Semua file selesai diproses!")