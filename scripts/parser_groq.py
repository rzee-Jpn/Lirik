import os
import json
import datetime
import time
import textwrap
from bs4 import BeautifulSoup
from groq import Groq
import requests

# ----------------------------
# 🔑 Setup API & Model
# ----------------------------
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY tidak ditemukan di environment.")

client = Groq(api_key=API_KEY)

# Ambil list model aktif dari Groq API (opsional)
def get_active_models():
    url = "https://api.groq.com/openai/v1/models"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        models = resp.json()
        # Filter hanya model teks (chat/completion)
        return [m["id"] for m in models if "text" in m.get("id", "").lower()]
    except Exception as e:
        print(f"⚠️ Gagal ambil model dari API: {e}")
        # fallback model default
        return ["llama-3.2-11b-text-preview", "llama-3.2-90b-text-preview"]

MODEL_CANDIDATES = get_active_models()

# ----------------------------
# 🔹 Utility
# ----------------------------
RAW_DIR = "data_raw"
OUT_DIR = "data_clean"
os.makedirs(OUT_DIR, exist_ok=True)

def safe_json_loads(text):
    try:
        return json.loads(text)
    except Exception:
        # fallback: coba cari blok JSON di text
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end])
            except Exception:
                return {}
        return {}

# ----------------------------
# 🔹 Request Groq
# ----------------------------
def groq_request(messages):
    for model in MODEL_CANDIDATES:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
                max_tokens=2048,
            )
            return resp.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Model {model} gagal: {e}")
            time.sleep(2)
    raise RuntimeError("❌ Semua model gagal dipakai.")

# ----------------------------
# 🔹 Parsing HTML
# ----------------------------
def parse_html_with_groq(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")

    # Pisahkan postingan berdasarkan tag umum
    posts = []
    for tag in soup.find_all(["article", "div", "section"]):
        text = tag.get_text(separator="\n", strip=True)
        if len(text) > 200:  # skip blok terlalu kecil
            posts.append(text)
    if not posts:  # fallback: seluruh teks
        posts = [soup.get_text(separator="\n", strip=True)]

    all_songs = []
    artist_info = {}
    print(f"📄 File dibagi jadi {len(posts)} postingan...")

    for idx, post_text in enumerate(posts, start=1):
        # Bagi postingan terlalu panjang
        chunks = textwrap.wrap(post_text, 8000)
        for i, chunk in enumerate(chunks, start=1):
            print(f"🧩 Parsing postingan {idx}/{len(posts)}, batch {i}/{len(chunks)}...")
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
                    {"role": "system", "content": "Kamu parser JSON disiplin, hanya keluarkan JSON valid."},
                    {"role": "user", "content": prompt}
                ])
                data = safe_json_loads(response_text)
                if not artist_info and "artist" in data:
                    artist_info = data["artist"]
                if "songs" in data:
                    all_songs.extend(data["songs"])
            except Exception as e:
                print(f"⚠️ Postingan {idx}, batch {i} gagal: {e}")
                continue

    return {
        "artist": artist_info,
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "songs": all_songs
    }

# ----------------------------
# 🔹 Main Process
# ----------------------------
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