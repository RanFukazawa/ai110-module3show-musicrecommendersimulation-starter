import pytest

from src.recommender import (
    Song,
    UserProfile,
    Recommender,
    load_songs,
    score_song,
    normalize_score,
    recommend_songs,
    MAX_SCORE,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Test Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def make_song(**overrides) -> dict:
    """Build a song dict with sensible defaults, overriding only what's needed."""
    base = {
        "id": 99,
        "title": "Test Song",
        "artist": "Test Artist",
        "genre": "pop",
        "mood": "happy",
        "energy": 0.5,
        "tempo_bpm": 100,
        "valence": 0.5,
        "danceability": 0.5,
        "acousticness": 0.5,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Recommender class (object-based interface) -- original starter tests
# ---------------------------------------------------------------------------

def test_recommend_returns_songs_sorted_by_score():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


def test_recommend_respects_k_larger_than_catalog():
    """Asking for more songs than exist should return every song, not error."""
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = make_small_recommender()
    results = rec.recommend(user, k=10)
    assert len(results) == 2  # catalog only has 2 songs


def test_recommend_with_empty_catalog_returns_empty_list():
    """An empty song list should return an empty list, not crash."""
    user = UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=False,
    )
    rec = Recommender(songs=[])
    results = rec.recommend(user, k=5)
    assert results == []


def test_explain_recommendation_no_match_returns_fallback_message():
    """A song matching nothing in the profile should still get a valid string."""
    user = UserProfile(
        favorite_genre="metal",
        favorite_mood="aggressive",
        target_energy=0.05,
        likes_acoustic=True,
    )
    rec = make_small_recommender()
    song = rec.songs[0]  # pop/happy/energy=0.8/acousticness=0.2 -- opposite of user
    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""


# ---------------------------------------------------------------------------
# score_song -- core weighting behavior
# ---------------------------------------------------------------------------

def test_score_song_full_match_hits_max_score():
    """A song matching genre, mood, energy exactly, with a compatible acoustic
    preference, should score at or very near MAX_SCORE."""
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}
    song = make_song(genre="pop", mood="happy", energy=0.8, acousticness=0.1)
    raw_score, reasons = score_song(user_prefs, song)

    assert raw_score == pytest.approx(5.0, abs=0.1)
    assert any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)


def test_score_song_genre_worth_more_than_mood():
    """Genre-only match should outscore mood-only match, confirming the 2:1 weighting."""
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.5}
    genre_match_song = make_song(genre="pop", mood="sad", energy=0.5)
    mood_match_song = make_song(genre="rock", mood="happy", energy=0.5)

    genre_score, _ = score_song(user_prefs, genre_match_song)
    mood_score, _ = score_song(user_prefs, mood_match_song)

    assert genre_score > mood_score


def test_score_song_energy_rewards_closeness_not_magnitude():
    """A song with energy closer to the target should score higher, even if
    its raw energy value is lower than a competing song's."""
    user_prefs = {"energy": 0.5}
    close_song = make_song(genre=None, mood=None, energy=0.55)   # distance 0.05
    far_high_song = make_song(genre=None, mood=None, energy=0.95)  # distance 0.45

    close_score, _ = score_song(user_prefs, close_song)
    far_score, _ = score_song(user_prefs, far_high_song)

    assert close_score > far_score


def test_score_song_acoustic_bonus_when_liked_and_acoustic():
    user_prefs = {"likes_acoustic": True}
    acoustic_song = make_song(genre=None, mood=None, acousticness=0.9)
    raw_score, reasons = score_song(user_prefs, acoustic_song)
    assert raw_score > 0
    assert any("matches your preference" in r for r in reasons)


def test_score_song_acoustic_penalty_when_disliked_and_acoustic():
    user_prefs = {"likes_acoustic": False}
    acoustic_song = make_song(genre=None, mood=None, acousticness=0.9)
    raw_score, reasons = score_song(user_prefs, acoustic_song)
    assert raw_score < 0
    assert any("more acoustic than you usually prefer" in r for r in reasons)


def test_score_song_acoustic_scales_continuously_not_as_flat_threshold():
    """A barely-acoustic song and a fully-acoustic song should get different
    penalties, not the same flat -0.5 -- confirms the continuous-gradient fix."""
    user_prefs = {"likes_acoustic": False}
    barely_acoustic = make_song(genre=None, mood=None, acousticness=0.2)
    fully_acoustic = make_song(genre=None, mood=None, acousticness=0.95)

    barely_score, _ = score_song(user_prefs, barely_acoustic)
    fully_score, _ = score_song(user_prefs, fully_acoustic)

    assert barely_score != fully_score
    assert fully_score < barely_score


# ---------------------------------------------------------------------------
# score_song -- edge cases
# ---------------------------------------------------------------------------

def test_score_song_missing_all_user_prefs_returns_zero():
    """An empty user_prefs dict should score every song at 0 with no reasons."""
    song = make_song()
    raw_score, reasons = score_song({}, song)
    assert raw_score == 0.0
    assert reasons == []


def test_score_song_missing_song_fields_does_not_crash():
    """A song dict missing expected keys should be handled via .get() without
    raising a KeyError."""
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}
    incomplete_song = {"title": "Mystery Track"}  # no genre/mood/energy/acousticness
    raw_score, reasons = score_song(user_prefs, incomplete_song)
    assert raw_score == 0.0
    assert reasons == []


def test_score_song_partial_user_prefs_only_scores_available_fields():
    """A user_prefs dict with only some keys should only score those features."""
    user_prefs = {"genre": "pop"}  # no mood, energy, or likes_acoustic
    song = make_song(genre="pop", mood="happy", energy=0.9, acousticness=0.9)
    raw_score, reasons = score_song(user_prefs, song)

    assert raw_score == 2.0  # only the genre bonus applies
    assert reasons == ["genre match (pop) (+2.0 pts)"]


def test_score_song_nonexistent_genre_scores_zero_for_that_component():
    """A genre that doesn't exist anywhere in the catalog should simply fail
    to match -- no crash, no special-case handling required."""
    user_prefs = {"genre": "vaporwave", "mood": "chill", "energy": 0.4}
    song = make_song(genre="lofi", mood="chill", energy=0.4)
    raw_score, reasons = score_song(user_prefs, song)

    assert not any("genre match" in r for r in reasons)
    assert any("mood match" in r for r in reasons)  # other features still score


def test_score_song_contradictory_profile_does_not_crash():
    """A self-contradictory profile (e.g. lofi genre + very high energy)
    should still produce a valid score, not raise an error."""
    user_prefs = {"genre": "lofi", "mood": "happy", "energy": 0.95, "likes_acoustic": False}
    song = make_song(genre="lofi", mood="chill", energy=0.3, acousticness=0.9)
    raw_score, reasons = score_song(user_prefs, song)

    assert isinstance(raw_score, float)
    assert isinstance(reasons, list)


def test_score_song_can_go_negative_before_clamping():
    """Raw score is allowed to go negative (e.g. a strong acoustic penalty
    with no other matches) -- clamping only happens in normalize_score."""
    user_prefs = {"genre": "metal", "mood": "aggressive", "energy": 0.0, "likes_acoustic": False}
    song = make_song(genre="classical", mood="melancholic", energy=1.0, acousticness=1.0)
    raw_score, _ = score_song(user_prefs, song)
    assert raw_score < 0


def test_score_song_never_double_counts_same_reason_source():
    """Each scoring component should contribute at most one reason string."""
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": True}
    song = make_song(genre="pop", mood="happy", energy=0.8, acousticness=0.9)
    _, reasons = score_song(user_prefs, song)
    assert len(reasons) == len(set(reasons))  # no duplicate reason strings


# ---------------------------------------------------------------------------
# normalize_score
# ---------------------------------------------------------------------------

def test_normalize_score_clamps_negative_to_zero():
    assert normalize_score(-2.5) == 0.0


def test_normalize_score_clamps_above_max_to_100():
    assert normalize_score(MAX_SCORE + 5) == 100.0


def test_normalize_score_max_score_maps_to_exactly_100():
    assert normalize_score(MAX_SCORE) == 100.0


def test_normalize_score_zero_maps_to_zero():
    assert normalize_score(0.0) == 0.0


def test_normalize_score_matches_expected_percentage():
    assert normalize_score(MAX_SCORE / 2) == pytest.approx(50.0, abs=0.1)


# ---------------------------------------------------------------------------
# recommend_songs -- functional / dict-based interface
# ---------------------------------------------------------------------------

def test_recommend_songs_returns_four_tuples():
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8, "likes_acoustic": False}
    songs = [make_song(id=1, genre="pop", mood="happy", energy=0.8)]
    results = recommend_songs(user_prefs, songs, k=5)

    assert len(results) == 1
    song, raw_score, pct_score, explanation = results[0]
    assert isinstance(song, dict)
    assert isinstance(raw_score, float)
    assert isinstance(pct_score, float)
    assert isinstance(explanation, str)


def test_recommend_songs_sorted_descending_by_raw_score():
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    songs = [
        make_song(id=1, genre="rock", mood="sad", energy=0.1),
        make_song(id=2, genre="pop", mood="happy", energy=0.8),
        make_song(id=3, genre="pop", mood="sad", energy=0.5),
    ]
    results = recommend_songs(user_prefs, songs, k=3)
    scores = [raw for _, raw, _, _ in results]
    assert scores == sorted(scores, reverse=True)


def test_recommend_songs_does_not_mutate_input_list():
    """sorted() should be used internally, never .sort(), so the caller's
    original songs list stays in its original order."""
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    songs = [
        make_song(id=1, genre="rock", mood="sad", energy=0.1),
        make_song(id=2, genre="pop", mood="happy", energy=0.8),
    ]
    original_order = [s["id"] for s in songs]
    recommend_songs(user_prefs, songs, k=2)
    assert [s["id"] for s in songs] == original_order


def test_recommend_songs_k_limits_result_count():
    user_prefs = {"genre": "pop"}
    songs = [make_song(id=i, genre="pop") for i in range(10)]
    results = recommend_songs(user_prefs, songs, k=3)
    assert len(results) == 3


def test_recommend_songs_empty_catalog_returns_empty_list():
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    results = recommend_songs(user_prefs, [], k=5)
    assert results == []


def test_recommend_songs_no_match_uses_fallback_explanation():
    """A song matching nothing should get the 'No strong matches found.'
    fallback explanation string, not an empty string."""
    user_prefs = {"genre": "metal", "mood": "aggressive", "energy": 1.0, "likes_acoustic": True}
    songs = [make_song(id=1, genre="pop", mood="happy", energy=0.0, acousticness=0.0)]
    results = recommend_songs(user_prefs, songs, k=1)
    _, _, _, explanation = results[0]
    assert explanation == "No strong matches found."


def test_recommend_songs_ties_are_both_returned():
    """Two songs with identical scores should both appear, rather than one
    being silently dropped."""
    user_prefs = {"genre": "pop"}
    songs = [
        make_song(id=1, title="Song A", genre="pop", mood=None, energy=None),
        make_song(id=2, title="Song B", genre="pop", mood=None, energy=None),
    ]
    results = recommend_songs(user_prefs, songs, k=2)
    assert len(results) == 2
    assert {r[0]["id"] for r in results} == {1, 2}


# ---------------------------------------------------------------------------
# load_songs
# ---------------------------------------------------------------------------

def test_load_songs_converts_numeric_fields(tmp_path):
    csv_content = (
        "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness\n"
        "1,Test Track,Test Artist,pop,happy,0.75,120,0.8,0.7,0.2\n"
    )
    csv_file = tmp_path / "songs.csv"
    csv_file.write_text(csv_content)

    songs = load_songs(str(csv_file))

    assert len(songs) == 1
    song = songs[0]
    assert isinstance(song["id"], int)
    assert isinstance(song["energy"], float)
    assert isinstance(song["tempo_bpm"], int)
    assert isinstance(song["valence"], float)
    assert song["genre"] == "pop"


def test_load_songs_empty_csv_returns_empty_list(tmp_path):
    """A CSV with only a header row (no data rows) should return an empty list."""
    csv_content = "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness\n"
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text(csv_content)

    songs = load_songs(str(csv_file))
    assert songs == []


def test_load_songs_missing_file_raises_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_songs("this/path/does/not/exist.csv")