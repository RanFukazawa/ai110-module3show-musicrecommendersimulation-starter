"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv") 

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    recommendations = recommend_songs(user_prefs, songs, k=5)

    print("=" * 100)
    print(f"User profile: {user_prefs}")
    print("=" * 100)
    print("\nTop Recommendations:\n")

    for rank, rec in enumerate(recommendations, start=1):
        # You decide the structure of each returned item.
        # A common pattern is: (song, score, explanation)
        song, score, explanation = rec
        print(f"{rank}. {song['title']} by {song['artist']}  —  Score: {score:.1f}%")
        print(f"   Because: {explanation}")
        print()


if __name__ == "__main__":
    main()