import os, json, datetime, time
from bs4 import BeautifulSoup
from groq import Groq

# 🔑 Ambil API key
API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY tidak ditemukan di environment.")
client = Groq(api_key=API_KEY)

# ✅ Model Groq aktif
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
            return resp.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Model {model} gagal: {e}")
            time.sleep(1)
    raise RuntimeError("❌ Semua model gagal dipakai.")

def detect_posts(soup):
    """
    Deteksi postingan otomatis.
    Kriteria:
    - <article> dianggap satu postingan
    - <div class="post"> dianggap satu postingan
    - <h2>, <h3>, atau <hr> sebagai pemisah
    """
    posts = []

    # Cek <article> dan <div class="post">
    posts.extend(soup.find_all("article"))
    posts.extend(soup.find_all("div", class_="post"))

    # Jika tidak ada, coba deteksi blok panjang
    if not posts:
        # Ambil semua tag anak <body>
        body_children = list(soup.body.children)
        block = []
        for tag in body_children:
            if tag.name in ["h2", "h3", "hr"]:
                if block:
                    posts.append(" ".join([b.get_text(separator="\n", strip=True) if hasattr(b, "get_text") else str(b) for b in block]))
                    block = []
            else:
                block.append(tag)
        if block:
            posts.append(" ".join([b.get_text(separator="\n", strip=True) if hasattr(b, "get_text") else str(b) for b in block]))

    return posts

def parse_html_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")
    posts = detect_posts(soup)
    print(f"📄 Ditemukan {len(posts)} postingan dalam file.")

    all_data = {"artist": {}, "songs": [], "updated_at": datetime.datetime.utcnow().isoformat() + "Z"}

    for i, post_text in enumerate(posts, start=1):
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
{post_text}
"""
        try:
            response_text = groq_request([
                {"role": "system", "content": "Kamu parser JSON yang disiplin dan hanya keluarkan JSON valid."},
                {"role": "user", "content": prompt}
            ])
            data = json.loads(response_text)

            if not all_data["artist"] and "artist" in data:
                all_data["artist"] = data["artist"]
            if "songs" in data:
                all_data["songs"].extend(data["songs"])

            print(f"✅ Postingan {i} berhasil diparsing.")
        except Exception as e:
            print(f"⚠️ Postingan {i} gagal diparsing: {e}")
            continue

    return all_data

# 🚀 Main process
html_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".html")]
print(f"📂 Ditemukan {len(html_files)} file HTML untuk diproses.")

for file_name in html_files:
    file_path = os.path.join(RAW_DIR, file_name)
    print(f"🔄 Memproses: {file_name}")

    parsed_data = parse_html_file(file_path)
    artist_name = parsed_data.get("artist", {}).get("nama_panggung", "unknown") or "unknown"
    out_file = os.path.join(OUT_DIR, f"{artist_name.replace(' ', '_').lower()}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Disimpan → {out_file}\n")

print("🎉 Semua file selesai diproses!")