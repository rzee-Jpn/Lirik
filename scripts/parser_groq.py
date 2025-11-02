import os
import json
from bs4 import BeautifulSoup
from datetime import datetime
from groq import Groq

# Ambil API key & model dari environment
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

def extract_text_from_html(file_path):
    """Ambil teks dari HTML (hapus tag, ambil konten utama)."""
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    # Ambil bagian teks utama
    text = soup.get_text(separator="\n", strip=True)
    return text

def parse_html_with_groq(html_text: str):
    """Gunakan Groq untuk parsing HTML jadi JSON lirik + info artis."""
    prompt = f"""
Kamu adalah asisten yang mengekstrak lirik lagu dari HTML dan mengubahnya menjadi JSON terstruktur.
Hasilkan JSON dengan format seperti ini:

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
  "updated_at": "{datetime.utcnow().isoformat()}Z",
  "songs": [
    {{
      "judul_lagu": "",
      "album": "",
      "tahun_rilis": "",
      "genre": "",
      "lirik_dengan_chord": "",
      "sumber": "lirik.html"
    }}
  ]
}}

Jika tidak ditemukan informasinya, isi dengan string kosong ("").
Pastikan format JSON valid.
Berikut konten HTML-nya:

---
{html_text}
---
"""

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "Kamu adalah parser HTML yang menghasilkan JSON lagu dan metadata artis."},
                {"role": "user", "content": prompt}
            ],
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"❌ Error parsing dengan model {MODEL}: {e}")
        return None


if __name__ == "__main__":
    data_raw_path = "data_raw/lirik.html"
    output_path = "data_clean/lirik_parsed.json"

    print("🔍 Parsing lirik.html...")

    if not os.path.exists(data_raw_path):
        print("⚠️ File data_raw/lirik.html tidak ditemukan.")
        exit(1)

    html_text = extract_text_from_html(data_raw_path)
    parsed_json_str = parse_html_with_groq(html_text)

    if not parsed_json_str:
        print("❌ Parsing gagal — tidak ada output dari Groq.")
        exit(1)

    # Coba ubah ke JSON
    try:
        parsed_data = json.loads(parsed_json_str)
    except json.JSONDecodeError:
        print("⚠️ Output tidak valid JSON, menyimpan sebagai teks mentah...")
        parsed_data = {"raw_output": parsed_json_str}

    os.makedirs("data_clean", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(parsed_data, f, ensure_ascii=False, indent=2)

    print(f"✅ Parsing selesai! Disimpan ke: {output_path}")