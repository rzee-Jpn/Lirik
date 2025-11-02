# scripts/utils/merge_utils.py
import json
from copy import deepcopy

def merge_dict(old, new):
    """Gabungkan dict dua arah (prioritas ke data baru, tapi tidak hapus lama)."""
    merged = deepcopy(old)
    for key, value in new.items():
        if isinstance(value, dict):
            merged[key] = merge_dict(old.get(key, {}), value)
        elif isinstance(value, list):
            if not value and key in old:
                merged[key] = old[key]
            else:
                merged[key] = list(set(old.get(key, []) + value))
        else:
            merged[key] = value or old.get(key, "")
    return merged

def merge_song_into_artist(existing, new_song):
    """Gabung 1 lagu ke artis"""
    songs = existing.get("songs", [])
    titles = [s.get("judul_lagu", "").lower() for s in songs]
    if new_song["judul_lagu"].lower() not in titles:
        songs.append(new_song)
    else:
        # update data lama
        idx = titles.index(new_song["judul_lagu"].lower())
        songs[idx] = merge_dict(songs[idx], new_song)
    existing["songs"] = songs
    return existing
