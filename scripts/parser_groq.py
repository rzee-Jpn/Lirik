import os, json, datetime, time
from bs4 import BeautifulSoup
from groq import Groq
import tiktoken
from concurrent.futures import ThreadPoolExecutor, as_completed

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GROQ_API_KEY tidak ditemukan di environment.")

client = Groq(api_key=API_KEY)

# Model terbaru Groq yang aktif
MODEL_CANDIDATES = [
    {"id": "llama-4-maverick-17b-128e-instruct", "max_tokens": 8192},
    {"id": "llama-4-scout-17b-16e-instruct", "max_tokens": 8192},
]

RAW_DIR = "data_raw"
OUT_DIR = "data_clean"
os.makedirs(OUT_DIR, exist_ok=True)

def count_tokens(text, encoding_name="cl100k_base"):
    enc = tiktoken.get_encoding(encoding_name)
    return len(enc.encode(text))

def split_text_by_tokens(text, max_tokens):
    lines = text.splitlines()
    chunks = []
    current = []
    current_tokens = 0
    for line in lines:
        line_tokens = count_tokens(line)
        if current_tokens + line_tokens > max_tokens:
            chunks.append("\n".join(current))
            current = [line]
            current_tokens = line_tokens
        else:
            current.append(line)
            current_tokens += line_tokens
    if current:
        chunks.append("\n".join(current))
    return chunks

def groq_request(messages):
    for model in MODEL_CANDIDATES:
        try:
            print(f"🧠 Coba model: {model['id']}")
            resp = client.chat.completions.create(
                model=model["id"],
                messages=messages,
                temperature=0.2,
                max_tokens=min(model["max_tokens"], 2048),
            )
            print(f"✅ Sukses pakai model: {model['id']}")
            return resp.choices[0].message.content
        except Exception as e:
            print(f"⚠️ Model {model['id']} gagal: {e}")
            time.sleep(1)
    raise RuntimeError("❌ Semua model gagal dipakai.")

def parse_chunk(chunk, idx, total):
    print(f"🧩 Parsing bagian {idx}/{total}...")
    prompt = f"""
Ekstrak informasi artis dan lagu dari teks ini. Hasilkan JSON valid:
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
            {"role": "system", "content": "Kamu parser JSON yang disiplin."},
            {"role": "user", "content": prompt}
        ])
        return json.loads(response_text)
    except Exception as e:
        print(f"⚠️ Bagian {idx} gagal: {e}")
        return None

def parse_html_with_groq(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "lxml")
    text = soup.get_text(separator="\n", strip=True)

    max_tokens = MODEL_CANDIDATES[0]["max_tokens"] - 512
    chunks = split_text_by_tokens(text, max_tokens)

    all_songs = []
    artist_info = {}
    print(f"📄 File dibagi jadi {len(chunks)} bagian...")

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(parse_chunk, chunk, i+1, len(chunks)) for i, chunk in enumerate(chunks)]
        for future in as_completed(futures):
            data = future.result()
            if not data:
                continue
            if not artist_info and "artist" in data:
                artist_info = data["artist"]
            if "songs" in data:
                all_songs.extend(data["songs"])

    return {
        "artist": artist_info,
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "songs": all_songs
    }

# Main process
html_files = [f for f in os.listdir(RAW_DIR) if f.lower().endswith(".html")]

for file_name in html_files:
    file_path = os.path.join(RAW_DIR, file_name)
    parsed_data = parse_html_with_groq(file_path)
    artist_name = parsed_data.get("artist", {}).get("nama_panggung", "unknown") or "unknown"
    out_file = os.path.join(OUT_DIR, f"{artist_name.replace(' ', '_').lower()}.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, indent=2, ensure_ascii=False)
    print(f"✅ Disimpan → {out_file}")

print("🎉 Semua file selesai diproses!")