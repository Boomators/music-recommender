"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import argparse
import textwrap

from src.recommender import load_songs, recommend_songs, max_score, MODES

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
    # Uses the advanced features: detailed tags, decade, popularity, instrumentalness
    "Nostalgic Night Owl": {
        "favorite_genre": "synthwave",
        "favorite_mood": "nostalgic",
        "target_energy": 0.55,
        "likes_acoustic": False,
        "favorite_tags": ["nostalgic", "nocturnal", "reflective"],
        "preferred_decade": 1990,
        "likes_popular": False,
        "wants_instrumental": True,
    },
    # Uses the explicit-lyrics filter
    "Clean Workout": {
        "favorite_genre": "pop",
        "favorite_mood": "intense",
        "target_energy": 0.9,
        "likes_acoustic": False,
        "favorite_tags": ["pumped", "adrenaline"],
        "allow_explicit": False,
    },
}


def print_recommendations(name: str, user_prefs: dict, recommendations: list, top: float) -> None:
    """Print a profile header followed by ranked songs, scores, and reasons."""
    prefs = ", ".join(f"{key}={value}" for key, value in user_prefs.items())
    print("=" * 60)
    print(f"Profile: {name}")
    print(f"  {prefs}")
    print("=" * 60)
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} by {song['artist']}  [{song['genre']}/{song['mood']}]")
        print(f"   Score: {score:.2f} / {top:.2f}")
        for reason in explanation.split("; "):
            print(f"     - {reason}")
    print()


TABLE_COLUMNS = [("#", 2), ("Song", 22), ("Genre / Mood", 18), ("Score", 11), ("Why", 46)]


def print_table(name: str, recommendations: list, top: float) -> None:
    """Print the recommendations as an ASCII table with one reason per line."""
    border = "+" + "+".join("-" * (width + 2) for _, width in TABLE_COLUMNS) + "+"

    def print_row(cells: list) -> None:
        wrapped = [
            [line for part in cell.split("\n") for line in textwrap.wrap(part, width) or [""]]
            for cell, (_, width) in zip(cells, TABLE_COLUMNS)
        ]
        for i in range(max(len(lines) for lines in wrapped)):
            parts = [
                (lines[i] if i < len(lines) else "").ljust(width)
                for lines, (_, width) in zip(wrapped, TABLE_COLUMNS)
            ]
            print("| " + " | ".join(parts) + " |")

    print(f"\n{name}")
    print(border)
    print_row([title for title, _ in TABLE_COLUMNS])
    print(border.replace("-", "="))
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print_row([
            str(rank),
            f"{song['title']}\nby {song['artist']}",
            f"{song['genre']}\n{song['mood']}",
            f"{score:.2f} / {top:.2f}",
            "\n".join(f"- {reason}" for reason in explanation.split("; ")),
        ])
        print(border)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Music Recommender Simulation")
    parser.add_argument("--mode", choices=sorted(MODES), default="genre-first",
                        help="ranking strategy (default: genre-first)")
    parser.add_argument("--diverse", action="store_true",
                        help="penalize repeated artists and genres in the top results")
    parser.add_argument("--profile", choices=sorted(PROFILES),
                        help="run a single profile instead of all of them")
    parser.add_argument("--format", choices=["list", "table"], default="list",
                        help="output layout (default: list)")
    parser.add_argument("-k", type=int, default=5, help="number of songs to recommend")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    mode = MODES[args.mode]
    songs = load_songs("data/songs.csv")
    print(f"Mode: {mode.name}{' + diversity penalty' if args.diverse else ''}")
    print()

    profiles = {args.profile: PROFILES[args.profile]} if args.profile else PROFILES
    for name, user_prefs in profiles.items():
        recommendations = recommend_songs(user_prefs, songs, args.k, mode, args.diverse)
        top = max_score(user_prefs, mode)
        if args.format == "table":
            print_table(name, recommendations, top)
        else:
            print_recommendations(name, user_prefs, recommendations, top)


if __name__ == "__main__":
    main()
