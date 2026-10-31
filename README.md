# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

**SongScout 1.0** is a content-based recommender that runs in the terminal. You give it a taste profile: a favorite genre, a mood, a target energy level, and acoustic or electronic sound. It scores each of the 18 songs with a simple point system and prints the top 5, each with the reasons that earned it points. I stress-tested it with six profiles, three of them designed to trick it, and ran one weight experiment. I documented what it gets right and wrong in the [model card](model_card.md).

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
Profile: High-Energy Pop
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

### Stress test: six profiles

I ran six profiles: three "normal" listeners and three adversarial ones designed to trick the scoring. Full output of `python -m src.main` with the baseline weights (genre 2.0, mood 1.0, energy 1.5, acoustic 0.5):

#### High-Energy Pop

```
============================================================
Profile: High-Energy Pop
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

Matches intuition. *Sunrise City* hits every signal. *Gym Hero* is second only because it's pop. A happy-pop listener would probably prefer *Rooftop Lights*, but "indie pop" ≠ "pop".

#### Chill Lofi

```
============================================================
Profile: Chill Lofi
  favorite_genre=lofi, favorite_mood=chill, target_energy=0.38, likes_acoustic=True
============================================================
1. Library Rain by Paper Lanterns  [lofi/chill]
   Score: 4.88 / 5.00
     - genre match: lofi (+2.00)
     - mood match: chill (+1.00)
     - energy 0.35 vs target 0.38 (+1.46)
     - acoustic texture (+0.43)
2. Midnight Coding by LoRoom  [lofi/chill]
   Score: 4.79 / 5.00
     - genre match: lofi (+2.00)
     - mood match: chill (+1.00)
     - energy 0.42 vs target 0.38 (+1.44)
     - acoustic texture (+0.35)
3. Focus Flow by LoRoom  [lofi/focused]
   Score: 3.86 / 5.00
     - genre match: lofi (+2.00)
     - energy 0.40 vs target 0.38 (+1.47)
     - acoustic texture (+0.39)
4. Spacewalk Thoughts by Orbit Bloom  [ambient/chill]
   Score: 2.81 / 5.00
     - mood match: chill (+1.00)
     - energy 0.28 vs target 0.38 (+1.35)
     - acoustic texture (+0.46)
5. Coffee Shop Stories by Slow Stereo  [jazz/relaxed]
   Score: 1.93 / 5.00
     - energy 0.37 vs target 0.38 (+1.48)
     - acoustic texture (+0.45)
```

The best-behaved profile. Lofi has 3 songs, so the whole top 3 is on-genre, and ambient/jazz fill in with the right low energy.

#### Deep Intense Rock

```
============================================================
Profile: Deep Intense Rock
  favorite_genre=rock, favorite_mood=intense, target_energy=0.9, likes_acoustic=False
============================================================
1. Storm Runner by Voltline  [rock/intense]
   Score: 4.93 / 5.00
     - genre match: rock (+2.00)
     - mood match: intense (+1.00)
     - energy 0.91 vs target 0.90 (+1.48)
     - electronic texture (+0.45)
2. Gym Hero by Max Pulse  [pop/intense]
   Score: 2.93 / 5.00
     - mood match: intense (+1.00)
     - energy 0.93 vs target 0.90 (+1.46)
     - electronic texture (+0.47)
3. Neon Euphoria by Pulse Theory  [edm/euphoric]
   Score: 1.92 / 5.00
     - energy 0.95 vs target 0.90 (+1.43)
     - electronic texture (+0.49)
4. Iron Tempest by Ashen Forge  [metal/aggressive]
   Score: 1.88 / 5.00
     - energy 0.97 vs target 0.90 (+1.40)
     - electronic texture (+0.48)
5. Sunrise City by Neon Echo  [pop/happy]
   Score: 1.79 / 5.00
     - energy 0.82 vs target 0.90 (+1.38)
     - electronic texture (+0.41)
```

One rock song, then a 2-point cliff. After *Storm Runner*, a pop workout song outranks the metal track a rock fan would likely want.

#### Sad but Hyped

```
============================================================
Profile: Sad but Hyped
  favorite_genre=folk, favorite_mood=sad, target_energy=0.9, likes_acoustic=False
============================================================
1. Paper Boats by Wren Alder  [folk/sad]
   Score: 3.63 / 5.00
     - genre match: folk (+2.00)
     - mood match: sad (+1.00)
     - energy 0.30 vs target 0.90 (+0.60)
     - electronic texture (+0.03)
2. Storm Runner by Voltline  [rock/intense]
   Score: 1.93 / 5.00
     - energy 0.91 vs target 0.90 (+1.48)
     - electronic texture (+0.45)
3. Gym Hero by Max Pulse  [pop/intense]
   Score: 1.93 / 5.00
     - energy 0.93 vs target 0.90 (+1.46)
     - electronic texture (+0.47)
4. Neon Euphoria by Pulse Theory  [edm/euphoric]
   Score: 1.92 / 5.00
     - energy 0.95 vs target 0.90 (+1.43)
     - electronic texture (+0.49)
5. Iron Tempest by Ashen Forge  [metal/aggressive]
   Score: 1.88 / 5.00
     - energy 0.97 vs target 0.90 (+1.40)
     - electronic texture (+0.48)
```

Adversarial: genre+mood point to a quiet song (energy 0.30), energy points to loud ones. Genre+mood win easily. *Paper Boats* is first despite being 0.60 away from the energy target.

#### Ghost Genre

```
============================================================
Profile: Ghost Genre
  favorite_genre=k-pop, favorite_mood=happy, target_energy=0.65, likes_acoustic=False
============================================================
1. Rooftop Lights by Indigo Parade  [indie pop/happy]
   Score: 2.66 / 5.00
     - mood match: happy (+1.00)
     - energy 0.76 vs target 0.65 (+1.33)
     - electronic texture (+0.33)
2. Sunrise City by Neon Echo  [pop/happy]
   Score: 2.66 / 5.00
     - mood match: happy (+1.00)
     - energy 0.82 vs target 0.65 (+1.25)
     - electronic texture (+0.41)
3. Concrete Crown by Verse Theory  [hip hop/confident]
   Score: 1.74 / 5.00
     - energy 0.78 vs target 0.65 (+1.30)
     - electronic texture (+0.44)
4. Night Drive Loop by Neon Echo  [synthwave/moody]
   Score: 1.74 / 5.00
     - energy 0.75 vs target 0.65 (+1.35)
     - electronic texture (+0.39)
5. Island Time by Coral Sound  [reggae/uplifting]
   Score: 1.69 / 5.00
     - energy 0.58 vs target 0.65 (+1.40)
     - electronic texture (+0.30)
```

Adversarial: "k-pop" isn't in the catalog, so nobody can earn the genre points and the max possible is 3.0. The system quietly falls back to mood + energy, which is reasonable, but it never tells the user their genre wasn't found.

#### Off the Scale

```
============================================================
Profile: Off the Scale
  favorite_genre=metal, favorite_mood=aggressive, target_energy=1.5, likes_acoustic=False
============================================================
1. Iron Tempest by Ashen Forge  [metal/aggressive]
   Score: 4.19 / 5.00
     - genre match: metal (+2.00)
     - mood match: aggressive (+1.00)
     - energy 0.97 vs target 1.50 (+0.70)
     - electronic texture (+0.48)
2. Neon Euphoria by Pulse Theory  [edm/euphoric]
   Score: 1.17 / 5.00
     - energy 0.95 vs target 1.50 (+0.67)
     - electronic texture (+0.49)
3. Gym Hero by Max Pulse  [pop/intense]
   Score: 1.12 / 5.00
     - energy 0.93 vs target 1.50 (+0.65)
     - electronic texture (+0.47)
4. Storm Runner by Voltline  [rock/intense]
   Score: 1.06 / 5.00
     - energy 0.91 vs target 1.50 (+0.61)
     - electronic texture (+0.45)
5. Sunrise City by Neon Echo  [pop/happy]
   Score: 0.89 / 5.00
     - energy 0.82 vs target 1.50 (+0.48)
     - electronic texture (+0.41)
```

Adversarial: target_energy = 1.5 is outside the 0–1 scale. The ranking is the same as for 1.0, but every energy score shrinks, and quiet songs get *negative* energy points (as low as −0.42). Nothing validates the input.

### Experiment: weight shift (energy ×2, genre ÷2)

I changed `ENERGY_WEIGHT` from 1.5 to 3.0 and `GENRE_WEIGHT` from 2.0 to 1.0. The max score became 5.5. Energy points still stay between 0 and 3.0 for any target inside 0–1, so the math holds up. Then I reverted to the baseline.

| Profile | Baseline top 3 | Experiment top 3 | Verdict |
|---|---|---|---|
| High-Energy Pop | Sunrise City, Gym Hero, Rooftop Lights | Sunrise City, **Rooftop Lights**, Gym Hero | More accurate: the happy indie-pop song passes the intense gym track |
| Chill Lofi | Library Rain, Midnight Coding, Focus Flow | *(same)* | No change; genre, mood and energy all agree |
| Deep Intense Rock | Storm Runner, Gym Hero, Neon Euphoria | *(same)* | No change; still no metal in the top 3 |
| Sad but Hyped | **Paper Boats**, Storm Runner, Gym Hero | Storm Runner, Gym Hero, Neon Euphoria (Paper Boats → #5) | Just different: energy now overrules the user's stated genre and mood |
| Ghost Genre | Rooftop Lights, Sunrise City, Concrete Crown | Rooftop Lights, Sunrise City, Night Drive Loop | Just different: bottom of the list reshuffles by energy |
| Off the Scale | Iron Tempest, Neon Euphoria, Gym Hero | *(same)* | No change |

**Takeaway:** Cutting genre fixed the "indie pop isn't pop" problem for one profile, but it broke the conflicting profile. There, energy alone now decides, and the only sad folk song falls to fifth. The shift mostly made results *different*, not better. The real fix is fuzzier genre matching, not a different weight. I kept the original weights.

---

## Limitations and Risks

- **Tiny, uneven catalog.** 18 songs, and 13 of the 15 genres have only one song, so most users get one good match and then filler.
- **Exact-match labels.** "indie pop" earns nothing for a pop fan, and "melancholic" earns nothing for a sad listener.
- **Same songs for everyone loud.** Below the first match, high-energy users all get the same few electronic tracks (*Gym Hero*, *Neon Euphoria*, *Storm Runner*).
- **No input checks.** An energy target of 1.5 is accepted and produces negative points. An unknown genre fails silently.
- **No understanding of lyrics, language or listening history.** It only knows four hand-assigned labels per song.

See the [model card](model_card.md) for details.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

A recommender doesn't really "predict" anything. It turns a song into a few numbers and labels, turns a person into a few target values, and measures how close they are. Ranking is just sorting those closeness scores. What surprised me is how much that feels like a real recommendation. The Chill Lofi list looks like something a streaming app would show, and listing the reasons next to each song makes it feel trustworthy, even though the logic is only addition.

The bias didn't come from the math. It came from the labels and the data. Because genres must match exactly and most genres have only one song, pop and lofi fans get rich, accurate lists, and everyone else gets one match plus generic loud or quiet filler. The weight experiment showed that changing the numbers moves the problem around rather than fixing it. In a real app with millions of songs, the same effect could quietly push listeners toward whatever genres are best labeled or most common, and away from smaller artists and styles.



