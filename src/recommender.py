import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict

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

def _user_profile_to_prefs(user: "UserProfile") -> Dict:
    """Convert a UserProfile dataclass into the dict shape score_song() expects."""
    return {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "energy": user.target_energy,
        "likes_acoustic": user.likes_acoustic,
    }

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k Song objects ranked against a UserProfile."""
        user_prefs = _user_profile_to_prefs(user)
 
        scored = [
            (song, score_song(user_prefs, asdict(song))[0])
            for song in self.songs
        ]
        ranked = sorted(scored, key=lambda pair: pair[1], reverse=True)
        return [song for song, _ in ranked[:k]]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable explanation of why a song scored the way it did."""
        user_prefs = _user_profile_to_prefs(user)
        _, reasons = score_song(user_prefs, asdict(song))
        if not reasons:
            return "This song didn't closely match your taste profile."
        return "Because it has " + "; ".join(reasons) + "."

def load_songs(csv_path: str) -> List[Dict]:
    """Load songs from a CSV file into a list of dicts with numeric fields converted.

    Required by src/main.py
 
    Reads each row as a dict of strings via csv.DictReader, then converts
    the numeric columns to float (or int for tempo_bpm) so later scoring
    logic can safely do math on them.
    """
    print(f"Loading songs from {csv_path}...")
    
    songs = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song = {
                "id": int(row["id"]),
                "title": row["title"],
                "artist": row["artist"],
                "genre": row["genre"],
                "mood": row["mood"],
                "energy": float(row["energy"]),
                "tempo_bpm": int(float(row["tempo_bpm"])),
                "valence": float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"])
            }
            songs.append(song)
    
    print(f"Loaded songs: {len(songs)}\n")

    return songs

MAX_SCORE = 5.5   # sum of every possible point contribution in score_song:
                  # genre (2.0) + mood (1.0) + energy (2.0) + acoustic (0.5)

def normalize_score(raw_score: float, max_score: float = MAX_SCORE) -> float:
    """Convert a raw point value into a 0-100% scale, clamped to that range.
 
    Clamped to the [0, 100] range: a raw score of 0 or below maps to 0%,
    since the acoustic penalty can push raw scores negative, and a
    percentage below 0 would not be meaningful to a user. Also used to
    convert individual per-feature point contributions (e.g. the +2.0 for
    a genre match) into the same percentage scale as the final score, so
    the reasons list stays consistent with the headline percentage.
    """
    percentage = (raw_score / max_score) * 100
    return round(max(0.0, min(100.0, percentage)), 1)

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score one song against a user's preferences using the weighted Algorithm Recipe.
 
    Required by recommend_songs() and src/main.py
 
    Algorithm Recipe (from Phase 2):
        - Genre match:   +2.0 points if song["genre"] == user_prefs["genre"]
        - Mood match:     +1.0 point  if song["mood"] == user_prefs["mood"]
        - Energy match:   up to 2.0 points, scaled by closeness between
                          song["energy"] and user_prefs["energy"]
                          (2.0 * (1 - |song.energy - user.target_energy|))
        - Acoustic bonus/penalty: up to +/- 0.5 points, scaled continuously
                          by how close song["acousticness"] is to the
                          user's implied target (1.0 if likes_acoustic,
                          0.0 if not) -- same distance-based approach as
                          the energy score, not a flat threshold
 
    Maximum possible score: 5.5
 
    Returns:
        (score, reasons) where score is the raw point total (max 5.5) and
        reasons is a list of short strings like "genre match (+2.0 pts)"
        expressed in raw points so the relative weight of each factor
        (e.g. genre worth 2x mood) is immediately visible. The final
        normalized percentage is computed separately in recommend_songs().
    """
    score = 0.0
    reasons = []
 
    # Genre match: +2.0 raw points
    user_genre = user_prefs.get("genre")
    song_genre = song.get("genre")
    if user_genre is not None and song_genre == user_genre:
        score += 2.0
        reasons.append(f"genre match ({song_genre}) (+2.0 pts)")
 
    # Mood match: +1.0 raw point
    user_mood = user_prefs.get("mood")
    song_mood = song.get("mood")
    if user_mood is not None and song_mood == user_mood:
        score += 1.0
        reasons.append(f"mood match ({song_mood}) (+1.0 pt)")
    
    # Energy similarity: up to 2.0 raw points, closer to target = higher score
    user_energy = user_prefs.get("energy")
    song_energy = song.get("energy")
    if user_energy is not None and song_energy is not None:
        distance = abs(song_energy - user_energy)
        similarity = max(0.0, 1 - distance)
        energy_points = round(2.0 * similarity, 2)
        score += energy_points
        if similarity > 0.8:
            reasons.append(f"very close energy match (+{energy_points} pts)")
        elif energy_points > 0:
            reasons.append(f"energy similarity (+{energy_points} pts)")
 
    # Acoustic bonus/penalty: up to +/- 0.5 raw points, scaled continuously
    # by how close song.acousticness is to the user's implied target
    # (1.0 if likes_acoustic, 0.0 if not) -- same distance-based approach
    # used for energy, rather than a flat threshold.
    likes_acoustic = user_prefs.get("likes_acoustic")
    song_acousticness = song.get("acousticness")
    if likes_acoustic is not None and song_acousticness is not None:
        acoustic_target = 1.0 if likes_acoustic else 0.0
        acoustic_distance = abs(song_acousticness - acoustic_target)
        acoustic_similarity = max(0.0, 1 - acoustic_distance)

        if likes_acoustic:
            acoustic_points = round(0.5 * acoustic_similarity, 2)
            score += acoustic_points
            if acoustic_points > 0.05:
                reasons.append(f"acoustic sound matches your preference (+{acoustic_points} pts)")
        else:
            # song_acousticness itself IS the distance from 0.0 (the target),
            # so the penalty scales directly with how acoustic the song is.
            acoustic_points = round(0.5 * song_acousticness, 2)
            score -= acoustic_points
            if acoustic_points > 0.05:
                reasons.append(f"more acoustic than you usually prefer (-{acoustic_points} pts)")
    
    return round(score, 2), reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, float, str]]:
    """Score, rank, and return the top-k songs for a given user preference dict.

    Required by src/main.py
 
    Scores every song in the catalog using score_song(), then sorts the
    full list highest-to-lowest by score and returns the top k.
 
    Uses sorted() rather than .sort() so the original `songs` list passed
    in by the caller is never mutated as a side effect -- sorted() returns
    a brand new list, leaving the input untouched.
 
    Returns:
        A list of (song_dict, raw_score, score_percent, explanation) tuples,
        length <= k, ordered from best match to worst match. raw_score is
        the point total out of MAX_SCORE (e.g. 5.4); score_percent is that
        same value normalized to a 0-100% scale. Both are provided so a
        caller can show whichever unit (or both) is most readable.
    """
    # Score every song in the catalog. Each entry becomes (song, raw_score, reasons).
    scored_songs = [(song, *score_song(user_prefs, song)) for song in songs]

    # Sort by RAW score, descending. Ranking uses the raw (unrounded-by-percent)
    # value so ties/near-ties aren't affected by percentage rounding.
    ranked_songs = sorted(scored_songs, key=lambda entry: entry[1], reverse=True)

    # Take the top k, keep the raw score, add the normalized percentage, and
    # join reasons into a single explanation string.
    top_k = ranked_songs[:k]
    results = [
        (
            song,
            raw_score,
            normalize_score(raw_score),
            "; ".join(reasons) if reasons else "No strong matches found.",
        )
        for song, raw_score, reasons in top_k
    ]
    
    return results