# scripts/parser_groq.py
import os, json, groq
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

from scripts.utils.schema_artist import base_artist_schema, base_song_schema
from scripts.utils.merge_utils import merge_dict, merge_song_into_artist

# === KONFIGURASI ===
DATA_RAW = Path("data_raw")
DATA_CLEAN = Path("data_clean/artists")
DATA_CLEAN.mkdir(parents=True, exist_ok=True)

client = groq.Client(api_key=os.getenv("GROQ_API_KEY"))

def parse_html_with_groq(file_path):
    """Baca HTML dan kirim ke Groq untuk diparse jadi JSON"""
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")
        text = soup.get_text("\n", strip=True)

    prompt = f"""
Kamu adalah asisten untuk mengekstrak informasi musik dari teks berikut.
Buat output JSON dengan struktur:
{{
  "artist": {{
    "nama_asli": "",
    "nama_panggung": "",
    "tanggal_lahir": "",
    "asal": "",
    "genre": [],
    "media_sosial": {{
      "instagram": "", "twitter": "", "youtube": "", "website": ""
    }},
    "label": "",
    "biografi": ""
  }},
  "songs": [
    {{
      "judul_lagu": "",
      "album": "",
      "tahun_rilis": "",
      "tipe": "",
      "track_number": "",
      "penulis_lirik": [],
      "komposer": [],
      "aransemen": [],
      "genre": [],
      "durasi": "",
      "label": "",
      "lirik_dengan_chord": "",
      "terjemahan": "",
      "sumber": "{os.path.basename(file_path)}",
      "tanggal_update": "{datetime.utcnow().isoformat()}Z",
      "tambahan": {{}}
    }}
  ]
}}

Isi data seakurat mungkin dari teks berikut.
Jika tidak ada informasi, biarkan string kosong.

Teks:
{text[:6000]}
"""

    resp = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    try:
        data = json.loads(resp.choices[0].message["content"])
        return data
    except Exception as e:
        print(f"⚠️ JSON gagal diparse dari {file_path}: {e}")
        return None

def save_artist_json(artist_name, data):
    slug = artist_name.lower().replace(" ", "-")
    path = DATA_CLEAN / f"{slug}.json"

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            old = json.load(f)
    else:
        old = base_artist_schema()

    merged = merge_dict(old, data)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"💾 Saved: {path}")

if __name__ == "__main__":
    files = list(DATA_RAW.glob("*.html"))
    for f in files:
        print(f"🔍 Parsing {f.name}...")
        parsed = parse_html_with_groq(f)
        if not parsed:
            continue

        artist_name = (
            parsed.get("artist", {}).get("nama_panggung")
            or parsed.get("artist", {}).get("nama_asli")
            or "unknown"
        )
        save_artist_json(artist_name, parsed)