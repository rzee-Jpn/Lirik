# smart_merger.py
import copy
from rapidfuzz import fuzz

MIN_CONFIDENCE = 60  # minimal score untuk anggap match strong


def merge_list_unique(old_list, new_list):
    if not old_list:
        old_list = []
    for item in new_list or []:
        if item and item not in old_list:
            old_list.append(item)
    return old_list


def merge_data(old, new):
    """Merge new into old without deleting existing fields when new is empty.
    - For dicts: recursive merge
    - For lists: unique append
    - For scalars: overwrite only if new not empty
    - Put unknown fields into extra_info
    """
    if old is None:
        old = {}
    merged = copy.deepcopy(old)

    for k, v in (new or {}).items():
        if k not in merged:
            # if v is empty, skip
            if v in (None, '', [], {}):
                continue
            merged[k] = v
            continue

        # both exist
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            merged[k] = merge_data(merged.get(k), v)
        elif isinstance(v, list) and isinstance(merged.get(k), list):
            merged[k] = merge_list_unique(merged.get(k), v)
        else:
            # scalar
            if v not in (None, ''):
                merged[k] = v
            # otherwise keep existing
    return merged


def merge_song_into_artist(artist_json, song_obj):
    """Place song object into artist's JSON under the correct album object.
    song_obj expects fields like: title, album, lyrics, language, extra_info, confidence
    """
    if not artist_json:
        artist_json = {'artist': song_obj.get('artist') or 'unknown', 'albums': [], 'update_terakhir': None}

    albums = artist_json.get('albums', [])
    album_title = song_obj.get('album') or 'singles'

    # find album
    album = None
    for a in albums:
        if a.get('judul_album') == album_title:
            album = a
            break
    if not album:
        album = {'judul_album': album_title, 'rilis': song_obj.get('release_date', ''), 'lagu': []}
        albums.append(album)

    # find existing song
    songs = album.get('lagu', [])
    existing = None
    for s in songs:
        if s.get('judul') and song_obj.get('title') and fuzz.ratio(s.get('judul'), song_obj.get('title')) > MIN_CONFIDENCE:
            existing = s
            break

    new_song_panel = {
        'judul': song_obj.get('title') or '',
        'lirik': song_obj.get('lyrics') or '',
        'lirik_meta': song_obj.get('lirik_meta', {}),
        'terjemahan': song_obj.get('translations', []),
        'extra_info': song_obj.get('extra_info', {}),
        'confidence': song_obj.get('confidence', {})
    }

    if existing:
        # merge smartly
        merged = merge_data(existing, new_song_panel)
        # replace existing in list
        idx = songs.index(existing)
        songs[idx] = merged
    else:
        songs.append(new_song_panel)

    album['lagu'] = songs
    artist_json['albums'] = albums
    artist_json['update_terakhir'] = song_obj.get('fetched_at')
    return artist_json
