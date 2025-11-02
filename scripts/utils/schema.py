def build_song_json(data):
    """Template JSON dengan auto-tambah field baru jika muncul di data."""
    template = {
        "judul_lagu": data.get("judul_lagu", ""),
        "artis": data.get("artis", ""),
        "album": data.get("album", ""),
        "tahun_rilis": data.get("tahun_rilis", ""),
        "studio": data.get("studio", ""),
        "penulis_lagu": data.get("penulis_lagu", []),
        "produser": data.get("produser", ""),
        "genre": data.get("genre", ""),
        "lirik_asli": data.get("lirik_asli", ""),
        "terjemahan": data.get("terjemahan", ""),
        "instrument_maker": data.get("instrument_maker", ""),
        "platform_streaming": data.get("platform_streaming", []),
        "media_sosial": data.get("media_sosial", []),
        "tanggal_update": data.get("tanggal_update", ""),
        "sumber": data.get("sumber", "")
    }

    # Auto tambah field yang belum ada di template
    for key, value in data.items():
        if key not in template:
            template[key] = value

    return template