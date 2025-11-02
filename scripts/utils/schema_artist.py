# scripts/utils/schema_artist.py
from datetime import datetime

def base_artist_schema():
    """Template fleksibel untuk data artis"""
    return {
        "artist": {
            "nama_asli": "",
            "nama_panggung": "",
            "tanggal_lahir": "",
            "asal": "",
            "genre": [],
            "media_sosial": {
                "instagram": "",
                "twitter": "",
                "youtube": "",
                "website": ""
            },
            "label": "",
            "biografi": ""
        },
        "songs": [],
        "updated_at": datetime.utcnow().isoformat() + "Z"
    }

def base_song_schema():
    """Template fleksibel untuk 1 lagu"""
    return {
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
        "sumber": "",
        "tanggal_update": datetime.utcnow().isoformat() + "Z",
        "tambahan": {}
    }
