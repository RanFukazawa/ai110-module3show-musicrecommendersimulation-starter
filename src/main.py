"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs

MAX_SCORE = 5.5

def main() -> None:
    songs = load_songs("data/songs.csv")

    # Baseline profiles + adversarial/edge-case profiles for Phase 4 evaluation.
    # Each entry is (label, user_prefs) so the label can be printed alongside results.
    user_profiles = [
        ("High-Energy Pop", {
            "genre": "pop", "mood": "happy", "energy": 0.85, "likes_acoustic": False,
        }),
        ("Chill Lofi", {
            "genre": "lofi", "mood": "chill", "energy": 0.3, "likes_acoustic": True,
        }),
        ("Deep Intense Rock", {
            "genre": "rock", "mood": "intense", "energy": 0.9, "likes_acoustic": False,
        }),
        # --- Adversarial / edge cases ---
        ("Contradictory Taste (lofi + max energy)", {
            "genre": "lofi", "mood": "happy", "energy": 0.95, "likes_acoustic": False,
        }),
        ("Nonexistent Genre", {
            "genre": "vaporwave", "mood": "chill", "energy": 0.4, "likes_acoustic": True,
        }),
        ("Missing Keys", {
            "genre": "pop",
        }),
    ]

    for label, user_prefs in user_profiles:
        recommendations = recommend_songs(user_prefs, songs, k=5)

        print("=" * 100)
        print(f"Profile: {label}")
        print(f"User prefs: {user_prefs}")
        print("=" * 100)
        print("\nTop Recommendations:\n")

        for rank, rec in enumerate(recommendations, start=1):
            song, raw_score, pct_score, explanation = rec
            print(
                f"{rank}. {song['title']} by {song['artist']}  —  "
                f"Score: {pct_score:.1f}% ({raw_score:.2f} / {MAX_SCORE} pts)"
            )
            print(f"   Because: {explanation}")
            print()


if __name__ == "__main__":
    main()