import os, json, glob
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

INPUT_DIR = "data_raw"
OUTPUT_DIR = "data_clean"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def extract_info(raw_text: str):
    prompt = f"""
Kamu adalah asisten yang mengekstrak informasi musik dari teks mentah (biasanya dari blog atau artikel lirik).
Bersihkan teks dari HTML, lalu ubah jadi struktur JSON berikut:

{{
  "Bio / Profil": {{
    "Nama lengkap & nama panggung": "",
    "Asal / domisili": "",
    "Tanggal lahir": "",
    "Genre musik": "",
    "Influences / inspirasi": "",
    "Cerita perjalanan musik": "",
    "Foto profil": "",
    "Link media sosial": {{
      "BandLab": "",
      "YouTube": "",
      "Spotify": "",
      "Instagram": ""
    }}
  }},
  "Diskografi": [
    {{
      "Nama album/single": "",
      "Tanggal rilis": "",
      "Label": "",
      "Jumlah lagu": "",
      "Cover art": "",
      "Produksi oleh / kolaborator tetap": "",
      "Lagu / Song List": [
        {{
          "Judul lagu": "",
          "Composer": "",
          "Lyricist": "",
          "Featuring": "",
          "Tahun rilis": "",
          "Album asal": "",
          "Durasi": "",
          "Genre": "",
          "Key": "",
          "Chord & lyrics": "",
          "Terjemahan": ""
        }}
      ]
    }}
  ]
}}

Aturan penting:
1. Jika teks menyebut nama artis (misal “Aimer”, “HYDE”), isi di “Nama lengkap & nama panggung”.
2. Jika teks memuat tanggal rilis (contoh “dirilis 18 Maret 2020”), isi di “Tanggal rilis”.
3. Jika teks menyebut durasi (misal “3:36 menit”), isi ke “Durasi”.
4. Jika ada bagian “KANJI”, “ROMAJI”, “Terjemahan”, simpan ke “Chord & lyrics” dan “Terjemahan”.
5. Jangan ubah bahasa lirik. Hanya bersihkan format HTML.
6. Jika beberapa lagu disebut, buat array “Lagu / Song List” berisi semuanya.
7. Pastikan output **hanya JSON valid**, tidak mengandung teks lain.

Sekarang proses teks berikut dan hasilkan JSON terstruktur:

{raw_text}

"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print("❌ Error:", e)
        return {"error": str(e), "raw_snippet": raw_text[:400]}

def main():
    files = glob.glob(f"{INPUT_DIR}/*.json")
    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_text = data.get("raw_text", "")
        parsed_info = extract_info(raw_text)
        output_path = os.path.join(OUTPUT_DIR, os.path.basename(path))
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump({"raw_text": raw_text, "parsed_info": parsed_info}, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved: {output_path}")

if __name__ == "__main__":
    main()