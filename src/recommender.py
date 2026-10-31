import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict, field

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: Optional[int] = None
    release_decade: Optional[int] = None
    mood_tags: List[str] = field(default_factory=list)
    instrumentalness: Optional[float] = None
    explicit: bool = False

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # Optional preferences: None (or empty) means "don't score this"
    favorite_tags: List[str] = field(default_factory=list)
    preferred_decade: Optional[int] = None
    likes_popular: Optional[bool] = None
    wants_instrumental: Optional[bool] = None
    allow_explicit: bool = True

@dataclass(frozen=True)
class ScoringMode:
    """A ranking strategy: the set of weights score_song applies."""
    name: str
    genre: float
    mood: float
    energy: float
    acoustic: float
    tags: float
    decade: float
    popularity: float
    instrumental: float

# Strategies (see README "Stretch Features"). Genre-first is the original Algorithm Recipe.
GENRE_FIRST = ScoringMode("genre-first", genre=2.0, mood=1.0, energy=1.5, acoustic=0.5,
                          tags=1.0, decade=0.5, popularity=0.3, instrumental=0.5)
MOOD_FIRST = ScoringMode("mood-first", genre=1.0, mood=2.0, energy=1.5, acoustic=0.5,
                         tags=1.5, decade=0.5, popularity=0.3, instrumental=0.5)
ENERGY_FOCUSED = ScoringMode("energy-focused", genre=1.0, mood=0.5, energy=3.0, acoustic=0.5,
                             tags=0.5, decade=0.5, popularity=0.3, instrumental=0.5)
MODES = {mode.name: mode for mode in (GENRE_FIRST, MOOD_FIRST, ENERGY_FOCUSED)}

ARTIST_REPEAT_PENALTY = 1.0
GENRE_REPEAT_PENALTY = 0.5

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5, mode: ScoringMode = GENRE_FIRST,
                  diverse: bool = False) -> List[Song]:
        """Return the top k songs for a user, highest score first."""
        by_id = {song.id: song for song in self.songs}
        results = recommend_songs(asdict(user), [asdict(s) for s in self.songs], k, mode, diverse)
        return [by_id[song["id"]] for song, _, _ in results]

    def explain_recommendation(self, user: UserProfile, song: Song,
                               mode: ScoringMode = GENRE_FIRST) -> str:
        """Return the scoring reasons for one song as a single readable string."""
        _, reasons = score_song(asdict(user), asdict(song), mode)
        return "; ".join(reasons)

INT_FIELDS = {"id", "popularity", "release_decade"}
FLOAT_FIELDS = {"energy", "tempo_bpm", "valence", "danceability", "acousticness", "instrumentalness"}

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV into dicts, converting numeric columns to int/float."""
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            for field_name in INT_FIELDS:
                row[field_name] = int(row[field_name])
            for field_name in FLOAT_FIELDS:
                row[field_name] = float(row[field_name])
            row["mood_tags"] = row["mood_tags"].split("|")
            row["explicit"] = row["explicit"] == "1"
            songs.append(row)
    print(f"Loaded songs: {len(songs)}")
    return songs

def max_score(user_prefs: Dict, mode: ScoringMode = GENRE_FIRST) -> float:
    """Return the highest score possible for this profile under this mode."""
    total = mode.genre + mode.mood + mode.energy + mode.acoustic
    if user_prefs.get("favorite_tags"):
        total += mode.tags
    if user_prefs.get("preferred_decade") is not None:
        total += mode.decade
    if user_prefs.get("likes_popular") is not None:
        total += mode.popularity
    if user_prefs.get("wants_instrumental") is not None:
        total += mode.instrumental
    return total

def score_song(user_prefs: Dict, song: Dict, mode: ScoringMode = GENRE_FIRST) -> Tuple[float, List[str]]:
    """Score one song against user preferences, returning (score, reasons)."""
    score = 0.0
    reasons = []

    if song["genre"] == user_prefs["favorite_genre"]:
        score += mode.genre
        reasons.append(f"genre match: {song['genre']} (+{mode.genre:.2f})")

    if song["mood"] == user_prefs["favorite_mood"]:
        score += mode.mood
        reasons.append(f"mood match: {song['mood']} (+{mode.mood:.2f})")

    # Closeness, not magnitude: full points at the target, shrinking linearly with distance
    energy_gap = abs(song["energy"] - user_prefs["target_energy"])
    energy_points = mode.energy * (1 - energy_gap)
    score += energy_points
    reasons.append(
        f"energy {song['energy']:.2f} vs target {user_prefs['target_energy']:.2f} (+{energy_points:.2f})"
    )

    if user_prefs.get("likes_acoustic", False):
        acoustic_points = mode.acoustic * song["acousticness"]
        label = "acoustic"
    else:
        acoustic_points = mode.acoustic * (1 - song["acousticness"])
        label = "electronic"
    score += acoustic_points
    reasons.append(f"{label} texture (+{acoustic_points:.2f})")

    # Detailed mood tags: partial credit for each of the user's tags the song shares
    wanted_tags = user_prefs.get("favorite_tags") or []
    shared_tags = [tag for tag in wanted_tags if tag in song.get("mood_tags", [])]
    if shared_tags:
        tag_points = mode.tags * len(shared_tags) / len(wanted_tags)
        score += tag_points
        reasons.append(f"shared tags: {', '.join(shared_tags)} (+{tag_points:.2f})")

    # Release decade: full points for the same decade, half for a neighboring one
    decade = user_prefs.get("preferred_decade")
    if decade is not None and song.get("release_decade") is not None:
        decade_gap = abs(song["release_decade"] - decade)
        if decade_gap <= 10:
            decade_points = mode.decade * (1.0 if decade_gap == 0 else 0.5)
            score += decade_points
            reasons.append(f"from the {song['release_decade']}s (+{decade_points:.2f})")

    likes_popular = user_prefs.get("likes_popular")
    if likes_popular is not None and song.get("popularity") is not None:
        share = song["popularity"] / 100
        popularity_points = mode.popularity * (share if likes_popular else 1 - share)
        score += popularity_points
        label = "popular pick" if likes_popular else "hidden gem"
        reasons.append(f"{label}, popularity {song['popularity']} (+{popularity_points:.2f})")

    wants_instrumental = user_prefs.get("wants_instrumental")
    if wants_instrumental is not None and song.get("instrumentalness") is not None:
        instrumental_points = mode.instrumental * (
            song["instrumentalness"] if wants_instrumental else 1 - song["instrumentalness"]
        )
        score += instrumental_points
        label = "instrumental" if wants_instrumental else "vocals"
        reasons.append(f"{label} (+{instrumental_points:.2f})")

    return score, reasons

def _rank_key(item: Tuple[Dict, float, List[str]], user_prefs: Dict) -> Tuple[float, float]:
    """Sort key: highest score first, ties go to the song closer to the target energy."""
    song, score, _ = item
    return score, -abs(song["energy"] - user_prefs["target_energy"])

def diversify(ranked: List[Tuple[Dict, float, List[str]]], user_prefs: Dict,
              k: int) -> List[Tuple[Dict, float, List[str]]]:
    """Greedily pick k songs, penalizing artists and genres already in the picked list."""
    picked = []
    pool = list(ranked)
    while pool and len(picked) < k:
        candidates = []
        for song, score, reasons in pool:
            notes = []
            if any(p["artist"] == song["artist"] for p, _, _ in picked):
                score -= ARTIST_REPEAT_PENALTY
                notes.append(f"artist already listed (-{ARTIST_REPEAT_PENALTY:.2f})")
            genre_repeats = sum(p["genre"] == song["genre"] for p, _, _ in picked)
            if genre_repeats:
                genre_penalty = GENRE_REPEAT_PENALTY * genre_repeats
                score -= genre_penalty
                notes.append(f"genre already listed x{genre_repeats} (-{genre_penalty:.2f})")
            candidates.append((song, score, reasons + notes))
        best = max(candidates, key=lambda item: _rank_key(item, user_prefs))
        picked.append(best)
        pool = [item for item in pool if item[0] is not best[0]]
    return picked

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5, mode: ScoringMode = GENRE_FIRST,
                    diverse: bool = False) -> List[Tuple[Dict, float, str]]:
    """Score every song, rank highest first, and return the top k as (song, score, explanation)."""
    # A hard filter, not a penalty: a -1.0 penalty still left explicit songs at #1
    if not user_prefs.get("allow_explicit", True):
        songs = [song for song in songs if not song.get("explicit")]
    scored = [(song, *score_song(user_prefs, song, mode)) for song in songs]
    scored.sort(key=lambda item: _rank_key(item, user_prefs), reverse=True)
    top = diversify(scored, user_prefs, k) if diverse else scored[:k]
    return [(song, score, "; ".join(reasons)) for song, score, reasons in top]
