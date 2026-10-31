from src.recommender import Song, UserProfile, Recommender

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
    # Starter expectation: the pop, happy, high energy song should score higher
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


from src.recommender import load_songs, recommend_songs, score_song, MOOD_FIRST


def test_load_songs_parses_advanced_features():
    songs = load_songs("data/songs.csv")
    song = songs[0]
    assert isinstance(song["popularity"], int)
    assert isinstance(song["release_decade"], int)
    assert isinstance(song["mood_tags"], list) and song["mood_tags"]
    assert isinstance(song["explicit"], bool)


def test_shared_tags_earn_partial_credit():
    prefs = {"favorite_genre": "x", "favorite_mood": "x", "target_energy": 0.5,
             "likes_acoustic": False, "favorite_tags": ["calm", "rainy"]}
    song = {"genre": "lofi", "mood": "chill", "energy": 0.5, "acousticness": 0.0,
            "mood_tags": ["calm", "cozy"]}
    score, reasons = score_song(prefs, song)
    # energy 1.5 + electronic 0.5 + half of the 1.0 tag weight
    assert score == 2.5
    assert any("shared tags: calm" in reason for reason in reasons)


def test_mood_first_mode_ranks_mood_match_above_genre_match():
    songs = load_songs("data/songs.csv")
    prefs = {"favorite_genre": "pop", "favorite_mood": "happy",
             "target_energy": 0.8, "likes_acoustic": False}
    titles = [song["title"] for song, _, _ in recommend_songs(prefs, songs, k=3, mode=MOOD_FIRST)]
    assert titles.index("Rooftop Lights") < titles.index("Gym Hero")


def test_explicit_songs_are_filtered_out():
    songs = load_songs("data/songs.csv")
    prefs = {"favorite_genre": "pop", "favorite_mood": "intense",
             "target_energy": 0.9, "likes_acoustic": False, "allow_explicit": False}
    results = recommend_songs(prefs, songs, k=len(songs))
    assert results
    assert not any(song["explicit"] for song, _, _ in results)


def test_diversity_penalty_avoids_repeat_artists():
    songs = load_songs("data/songs.csv")
    prefs = {"favorite_genre": "pop", "favorite_mood": "happy",
             "target_energy": 0.8, "likes_acoustic": False}
    artists = [song["artist"] for song, _, _ in recommend_songs(prefs, songs, k=5, diverse=True)]
    assert len(artists) == len(set(artists))
