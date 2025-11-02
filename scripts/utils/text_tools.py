import re

def extract_lyrics_info(text, filename=""):
    """Ekstraksi sederhana dari teks/artikel mentah."""

    title = re.search(r"(?i)(?:title|judul)\s*[:\-–]\s*(.*)", text)
    artist = re.search(r"(?i)(?:artist|penyanyi|by)\s*[:\-–]\s*(.*)", text)
    album = re.search(r"(?i)(?:album)\s*[:\-–]\s*(.*)", text)
    year = re.search(r"(?i)(?:year|tahun)\s*[:\-–]\s*(\d{4})", text)

    lyrics = []
    for line in text.splitlines():
        if len(line.strip()) > 1:
            lyrics.append(line.strip())

    return {
        "judul_lagu": title.group(1).strip() if title else filename.replace(".txt", ""),
        "artis": artist.group(1).strip() if artist else "",
        "album": album.group(1).strip() if album else "",
        "tahun_rilis": year.group(1) if year else "",
        "lirik_asli": "\n".join(lyrics),
        "terjemahan": "",
        "sumber": "manual_file",
    }
