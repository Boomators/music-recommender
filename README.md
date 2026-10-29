# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommenders like Spotify or YouTube mix two big ideas. **Collaborative filtering** looks at behavior across millions of users ("people who played what you played also played X"), while **content-based filtering** looks at the songs themselves: their genre, tempo, energy, and audio fingerprint. At scale they also use skips, replays, playlist adds, and time of day, and they run in stages: first narrow millions of tracks down to a few hundred candidates, then score and rank those carefully. My simulation is a small **content-based** recommender. It has no other users to learn from, so it compares one user's stated taste profile directly against each song's attributes. It weighs **genre** most heavily because that's the strongest "this is my kind of music" signal, then **mood**, then how close the song's **energy** is to what the user wants. Acoustic texture acts as a smaller tiebreaker.

### Features used

**`Song`**
- `genre` (categorical): pop, lofi, rock, ambient, jazz, synthwave, indie pop, hip hop, classical, metal, country, reggae, edm, r&b, folk
- `mood` (categorical): happy, chill, intense, relaxed, moody, focused, confident, melancholic, aggressive, nostalgic, uplifting, euphoric, romantic, sad
- `energy` (0.0–1.0): how intense or active the track feels
- `acousticness` (0.0–1.0): acoustic/organic vs. electronic/produced
- *Loaded but not scored (yet):* `tempo_bpm`, `valence`, `danceability`. Tempo mostly tracks energy in this dataset, so it adds little new information. Valence could help separate "high energy and happy" from "high energy and dark", so it's a good candidate for an experiment.

**`UserProfile`**
- `favorite_genre`: matched against `song.genre`
- `favorite_mood`: matched against `song.mood`
- `target_energy` (0.0–1.0): the energy level the user wants right now
- `likes_acoustic` (bool): whether they prefer acoustic or electronic textures

### Algorithm Recipe

**Scoring Rule (one song → one number):**

| Signal | Points |
|---|---|
| Genre matches `favorite_genre` | +2.0 |
| Mood matches `favorite_mood` | +1.0 |
| Energy closeness | +1.5 × (1 − \|song.energy − target_energy\|) |
| Acoustic fit | +0.5 × acousticness if `likes_acoustic`, else +0.5 × (1 − acousticness) |

The highest possible score is **5.0**. The energy term rewards *closeness*, not "more is better". A song that exactly matches the target gets the full 1.5, and the points shrink linearly the further away it is. So a user who wants 0.4 energy prefers a 0.42 lofi track over a 0.93 gym anthem.

Genre outweighs mood (2.0 vs 1.0) because genre is a more stable part of someone's taste. A pop fan in a chill mood still mostly wants pop. The risk is a "genre bubble", which I'll test in the Experiments section.

**Ranking Rule (all scores → recommendations):** Score every song, sort from highest to lowest, break ties by energy closeness, and return the top `k`. Each recommendation also lists the reasons that earned points (e.g. "genre match (+2.0), energy close to target (+1.47)").

**Why both rules?** The scoring rule only judges *one song in isolation*. It can say a song is a 4.2 but not whether that's good *compared to the rest of the catalog*. The ranking rule turns those separate judgments into a decision: which `k` songs to show, and in what order. Keeping them separate also means either one can change on its own, for example adding a diversity rule that stops two songs by the same artist from appearing back to back, without touching how individual songs are scored.

### Example taste profile

```python
user_prefs = {
    "favorite_genre": "lofi",
    "favorite_mood": "chill",
    "target_energy": 0.38,
    "likes_acoustic": True,
}
```

**Can it tell "chill lofi" from "intense rock"?** Yes. I ran the recipe by hand on all 18 songs:

| Profile | #1 | #2 | #3 | Gap from #1 to #4 |
|---|---|---|---|---|
| lofi / chill / 0.38 / acoustic | Library Rain 4.88 | Midnight Coding 4.79 | Focus Flow 3.86 | 2.07 |
| rock / intense / 0.90 / electronic | Storm Runner 4.93 | Gym Hero 2.93 | Neon Euphoria 1.92 | 3.05 |

The two lists don't share a single song. Energy and acousticness point in opposite directions for the two profiles, so even songs that don't match on genre or mood land on the correct side.

**Weak spots in the profile:**
- **Too narrow when the genre is rare.** The rock profile finds its one rock song and then falls back on energy alone. That ranks *Iron Tempest* (metal, aggressive), which a rock fan would probably like, below a pop song. Genre is an exact text match, so "rock" earns no points for "metal" and "pop" earns none for "indie pop".
- **Single values only.** The profile holds one genre and one mood, so it can't say "lofi *or* jazz".
- **Mood labels are exact matches too.** "sad" earns nothing for "melancholic", even though the meanings are close. A sad-mood listener gets *Paper Boats* first, but *Rainfall Sonata* only by luck of its low energy.

### Data flow

```
INPUT                     PROCESS (the loop)                         OUTPUT (the ranking)
─────                     ──────────────────                         ────────────────────
user_prefs ─────┐
                │   for each song in songs.csv:
songs.csv ──► load_songs() ──► score_song(user_prefs, song)
                │                 ├─ genre match?      +2.0
                │                 ├─ mood match?       +1.0
                │                 ├─ energy closeness  +0..1.5
                │                 └─ acoustic fit      +0..0.5
                │              → (score, reasons)                    sort by score (desc)
                └──────────────── collect all 18 results ──────────► take top k
                                                                     → [(song, score, explanation), ...]
```

### Expected biases

These come from the weights and the dataset. I plan to check each one once the code runs.

- **Genre over-prioritization.** Take two songs with the same energy. A song in the right genre but the wrong mood (about 3.5) still beats a song in the wrong genre with the right mood (about 2.5). This system might ignore great songs that match the user's mood just because they're filed under a different genre.
- **Exact-match labels.** Genre and mood are compared as plain strings, so "rock" gets nothing for "metal", "pop" gets nothing for "indie pop", and "sad" gets nothing for "melancholic". The system can't tell when two labels are close in meaning, so it penalizes songs that are actually close fits.
- **Uneven catalog.** Lofi has 3 songs and pop has 2, but 13 other genres have only 1 each. Lofi and pop fans get a full, well-matched top 3, while everyone else gets one genre hit followed by songs ranked mostly on energy.
- **Energy dominates the fallback.** Once genre and mood stop separating songs, the energy term (up to 1.5) does most of the work, so songs with similar energy but very different feel get grouped together. *Iron Tempest* (metal, dark) and *Neon Euphoria* (edm, euphoric) are an example.
- **Ignored features.** Valence, tempo and danceability are loaded but never scored, so the system can't tell a bright 0.75-energy song from a dark one unless the mood label happens to say so.
- **Hand-labeled data.** Genres, moods and numbers were assigned by hand or by an AI. Whoever labeled them chose what counts as "chill" or "intense", and the recommender inherits those choices.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Output of `python -m src.main` for the default pop/happy profile:

```
Loaded songs: 18

============================================================
Profile: Default pop/happy
  favorite_genre=pop, favorite_mood=happy, target_energy=0.8, likes_acoustic=False
============================================================
1. Sunrise City by Neon Echo  [pop/happy]
   Score: 4.88 / 5.00
     - genre match: pop (+2.00)
     - mood match: happy (+1.00)
     - energy 0.82 vs target 0.80 (+1.47)
     - electronic texture (+0.41)
2. Gym Hero by Max Pulse  [pop/intense]
   Score: 3.78 / 5.00
     - genre match: pop (+2.00)
     - energy 0.93 vs target 0.80 (+1.30)
     - electronic texture (+0.47)
3. Rooftop Lights by Indigo Parade  [indie pop/happy]
   Score: 2.77 / 5.00
     - mood match: happy (+1.00)
     - energy 0.76 vs target 0.80 (+1.44)
     - electronic texture (+0.33)
4. Concrete Crown by Verse Theory  [hip hop/confident]
   Score: 1.91 / 5.00
     - energy 0.78 vs target 0.80 (+1.47)
     - electronic texture (+0.44)
5. Night Drive Loop by Neon Echo  [synthwave/moody]
   Score: 1.81 / 5.00
     - energy 0.75 vs target 0.80 (+1.42)
     - electronic texture (+0.39)
```

These results match what I expected. *Sunrise City* matches on every signal. *Gym Hero* gets the genre match but loses points for being too intense. *Rooftop Lights* would arguably suit a pop fan better than *Gym Hero*, but "indie pop" doesn't count as a "pop" match. That's the exact-match bias I predicted, showing up in practice.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



