import os, json, datetime, time
from bs4 import BeautifulSoup
from groq import Groq

# 🧠 Model fallback system — urut dari yang paling bagus
MODEL_CANDIDATES = [
    "llama-3.1-70b-versatile",   # utama
    "gemma2-9b-it",              # cepat, pintar
    "llama-3.1-8b-instant",      # darurat
]

# 🔑 Ambil API key dari env
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY tidak ditemukan di environment.")

client = Groq(api_key=API_KEY)

# 📁 Folder input/output
RAW_DIR = "data_raw"
OUT_DIR = "data_clean"
os.makedirs(OUT_DIR, exist_ok=True)

# 🧠 fungsi fallback otomatis
def groq_request(messages):
    for model in MODEL_CANDIDATES:
        try:
            print(f"🧠 Mencoba model: {model}")
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=2048,
            )
            print(f"✅ Berhasil pakai model: {model}")
            return resp.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Model {model} gagal: {e}")
            time.sleep(2)
    raise RuntimeError("❌ Semua model Groq gagal dipakai.")

# 🧩 fungsi untuk parse HTML
def parse_html_with_groq(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator="\n", strip=True)

    prompt = f"""
Kamu adalah parser yang mengekstrak data artis dan lagu dari teks berikut.

Tugasmu:
1. Deteksi nama artis dan semua metadata (nama asli, tanggal lahir, nama panggung, asal, label, media sosial).
2. Ambil daftar lagu dan untuk tiap lagu tulis:
   - judul_lagu
   - album (jika ada)
   - tahun_rilis
   - pembuat_lirik
   - composer
   - arranger
   - aransemen
   - lirik_dengan_chord (preserve format chord di atas lirik)
3. Jika ada data tidak ditemukan, tulis string kosong.

Output dalam format JSON seperti ini:
{{
  "artist": {{
    "nama_asli": "...",
    "nama_panggung": "...",
    "tanggal_lahir": "...",
    "asal": "...",
    "label": "...",
    "media_sosial": {{}}
  }},
  "updated_at": "{datetime.datetime.utcnow().isoformat()}Z",
  "songs": [
    {{
      "judul_lagu": "...",
      "album": "...",
      "tahun_rilis": "",
      "pembuat_lirik": "",
      "composer": "",
      "arranger": "",
      "aransemen": "",
      "lirik_dengan_chord": "..."
    }}
  ]
}}

Berikut teks yang perlu diproses:
{text[:30000]}
"""

    try:
        response_text = groq_request([
            {"role": "system", "content": "Kamu adalah parser JSON yang disiplin dan hanya mengeluarkan JSON valid."},
            {"role": "user", "content": prompt}
        ])
        data = json.loads(response_text)
        return data
    except Exception as e:
        print(f"❌ Gagal parsing {file_path}: {e}")
        return None

# 🚀 Main process
print("📂 Mendeteksi file HTML di folder:", RAW_DIR)
html_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".html")]
print(f"🔍 Ditemukan {len(html_files)} file HTML untuk diproses.\n")

for file_name in html_files:
    file_path = os.path.join(RAW_DIR, file_name)
    print(f"🔄 Memproses: {file_name}")

    parsed_data = parse_html_with_groq(file_path)
    if parsed_data:
        artist_name = parsed_data.get("artist", {}).get("nama_panggung", "unknown").strip() or "unknown"
        output_file = os.path.join(OUT_DIR, f"{artist_name.replace(' ', '_').lower()}.json")
        with open(output_file, "w", encoding="utf-8") as out:
            json.dump(parsed_data, out, indent=2, ensure_ascii=False)
        print(f"✅ Disimpan → {output_file}\n")
    else:
        print(f"⚠️ Tidak bisa parse file {file_name}\n")

print("🎉 Semua file selesai diproses!")