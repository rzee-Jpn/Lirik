import os, json, datetime, time, textwrap, requests
from bs4 import BeautifulSoup
from groq import Groq

# 🔑 Ambil API key
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY tidak ditemukan di environment.")

client = Groq(api_key=API_KEY)

RAW_DIR = "data_raw"
OUT_DIR = "data_clean"
os.makedirs(OUT_DIR, exist_ok=True)

# 🔹 Ambil daftar model aktif dari GroqCloud
def get_active_models():
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(url, headers=headers)
    data = response.json()
    active_models = [m["id"] for m in data.get("data", []) if not m.get("deprecated", False)]
    if not active_models:
        raise RuntimeError("❌ Tidak ada model aktif ditemukan.")
    return active_models

MODEL_CANDIDATES = get_active_models()
print(f"✅ Model aktif ditemukan: {MODEL_CANDIDATES}")

# 🔹 Request ke Groq dengan retry dan skip model gagal
def groq_request(messages):
    tried_models = []
    for model in MODEL_CANDIDATES:
        if model in tried_models:
            continue
        tried_models.append(model)
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
            msg = str(e)
            if "404" in msg or "decommissioned" in msg.lower():
                print(f"⚠️ Model {model} tidak tersedia atau sudah deprecated, skip.")
                continue
            print(f"⚠️ Model {model} gagal karena {msg}, coba model lain.")
            time.sleep(2)
    raise RuntimeError("❌ Semua model gagal dipakai.")

# 🔹 Parser HTML
def parse_html_with_groq(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator="\n", strip=True)

    chunks = textwrap.wrap(text, 8000)
    all_songs = []
    artist_info = {}

    print(f"📄 File dibagi jadi {len(chunks)} bagian...")

    for i, chunk in enumerate(chunks, start=1):
        print(f"🧩 Parsing bagian {i}/{len(chunks)}...")
        prompt = f"""
Ekstrak semua informasi artis dan lagu dari teks ini.
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
                {"role": "system", "content": "Kamu parser JSON yang disiplin dan hanya keluarkan JSON valid."},
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
print(f"📂 Ditemukan {len(html_files)} file HTML untuk diproses.\n")

for file_name in html_files:
    file_path = os.path.join(RAW_DIR, file_name)
    print(f"🔄 Memproses: {file_name}")

    parsed_data = parse_html_with_groq(file_path)
    artist_name = parsed_data.get("artist", {}).get("nama_panggung", "unknown") or "unknown"
    out_file = os.path.join(OUT_DIR, f"{artist_name.replace(' ', '_').lower()}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Disimpan → {out_file}\n")

print("🎉 Semua file selesai diproses!")