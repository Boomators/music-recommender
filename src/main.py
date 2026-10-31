"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from src.recommender import load_songs, recommend_songs, MAX_SCORE

# Taste profiles (keys mirror UserProfile fields)
PROFILES = {
    "High-Energy Pop": {
        "favorite_genre": "pop",
        "favorite_mood": "happy",
        "target_energy": 0.8,
        "likes_acoustic": False,
    },
    "Chill Lofi": {
        "favorite_genre": "lofi",
        "favorite_mood": "chill",
        "target_energy": 0.38,
        "likes_acoustic": True,
    },
    "Deep Intense Rock": {
        "favorite_genre": "rock",
        "favorite_mood": "intense",
        "target_energy": 0.9,
        "likes_acoustic": False,
    },
    # Adversarial: genre and mood point to a quiet song, energy points to loud ones
    "Sad but Hyped": {
        "favorite_genre": "folk",
        "favorite_mood": "sad",
        "target_energy": 0.9,
        "likes_acoustic": False,
    },
    # Adversarial: genre that doesn't exist in the catalog
    "Ghost Genre": {
        "favorite_genre": "k-pop",
        "favorite_mood": "happy",
        "target_energy": 0.65,
        "likes_acoustic": False,
    },
    # Adversarial: energy target outside the 0.0-1.0 scale
    "Off the Scale": {
        "favorite_genre": "metal",
        "favorite_mood": "aggressive",
        "target_energy": 1.5,
        "likes_acoustic": False,
    },
}


def print_recommendations(name: str, user_prefs: dict, recommendations: list) -> None:
    """Print a profile header followed by ranked songs, scores, and reasons."""
    prefs = ", ".join(f"{key}={value}" for key, value in user_prefs.items())
    print("=" * 60)
    print(f"Profile: {name}")
    print(f"  {prefs}")
    print("=" * 60)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} by {song['artist']}  [{song['genre']}/{song['mood']}]")
        print(f"   Score: {score:.2f} / {MAX_SCORE:.2f}")
        for reason in explanation.split("; "):
            print(f"     - {reason}")
    print()


def main() -> None:
    songs = load_songs("data/songs.csv")
    print()

    for name, user_prefs in PROFILES.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)
        print_recommendations(name, user_prefs, recommendations)


if __name__ == "__main__":
    main()
