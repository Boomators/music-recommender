# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  


**SongScout 1.0**: a tiny scorecard-based music recommender.

---

## 2. Intended Use  


**Goal / task:** SongScout suggests songs a listener will probably like. You describe your taste: a favorite genre, a mood, an energy level, and acoustic or electronic sound. It scores all 18 songs in its catalog and returns the top 5, each with the reasons it was picked.

**Assumptions about the user:**
- They can describe their taste with one genre and one mood.
- Their taste doesn't change. There is no listening history and no learning over time.
- They use the same words as the catalog ("pop", not "indie pop" or "k-pop").

**Intended use:**
- A classroom project for learning how content-based recommenders work.
- Experimenting with weights and seeing how rankings change.
- Talking about bias in small, readable systems.

**Not intended for:**
- Real users or a real music app. The catalog is 18 made-up songs.
- Judging what music is "good". It only measures how close a song is to one stated preference.
- Anything that needs fairness to artists. Its rankings favor whichever genres happen to have more songs.
- Inputs it doesn't check, such as energy values outside 0–1.

---

## 3. How the Model Works  

Think of the recommender as a judge holding a scorecard. You tell it four things about your taste: your favorite genre, the mood you're in, how energetic you want the music to be (from 0 for very calm to 1 for very intense), and whether you prefer acoustic or electronic sound. The judge then looks at every song in the catalog, one at a time, and hands out points:

- **Genre:** 2 points if the song is in your favorite genre. This is the biggest prize, because genre is usually the most stable part of someone's taste.
- **Mood:** 1 point if the song's mood matches yours.
- **Energy:** up to 1.5 points for being *close* to the energy you asked for. A perfect match gets all 1.5, and the points shrink the further off the song is. Being louder or calmer doesn't earn extra points; only being close does.
- **Sound:** up to 0.5 points for leaning the way you like. Acoustic fans get more for acoustic songs, and electronic fans get more for produced ones.

A perfect song scores 5 out of 5. After every song has a score, the judge lines them up from highest to lowest and shows you the top five. If two songs tie, the one closer to your energy target goes first. Each recommendation comes with its scorecard, for example "genre match (+2.00), energy 0.82 vs target 0.80 (+1.47)", so you can see exactly why it was picked.

**Changes from the starter logic:** The starter code just returned the first few songs in the file. I replaced that with the scoring rules above, added acoustic preference as a fourth, smaller factor, made every score come with its reasons, and added the energy tie-breaker so ties aren't decided by where a song happens to sit in the file.

---

## 4. Data  


- **Size:** 18 songs in `data/songs.csv`. The starter file had 10. I added 8, each with a genre and mood that wasn't there before.
- **Features per song:** genre, mood, energy (0–1), tempo (BPM), valence (0–1, how bright the song sounds), danceability (0–1), and acousticness (0–1).
- **Used in scoring:** genre, mood, energy and acousticness. Tempo, valence and danceability are loaded but ignored.
- **Coverage:** 15 genres and 14 moods. Lofi has 3 songs and pop has 2. Every other genre has exactly 1.
- **What's missing:**
  - lyrics, language and vocals
  - artist popularity and release era
  - listening history from any real people
  - many big genres (Latin, K-pop, gospel and more)
- **Where it came from:** every value was invented, by the course or by an AI assistant. Someone decided what "chill" or "0.82 energy" means, and the recommender inherits those choices.

---

## 5. Strengths  


- **Clear-cut profiles work well.** Chill Lofi gets three lofi songs and then calm ambient and jazz. High-Energy Pop gets *Sunrise City*, a perfect match, at #1.
- **Opposite tastes get opposite lists.** The pop and lofi profiles share no songs, and neither do the rock and lofi profiles.
- **Energy works as "closeness", not "louder is better".** A user who wants 0.38 energy never sees a 0.93 song near the top.
- **Every pick is explained.** Each song shows exactly which rules gave it points, so it's easy to see why it ranked where it did.
- **It fails gracefully.** An unknown genre or contradictory preferences still produce a sensible list instead of crashing.

---

## 6. Limitations and Bias 

**Main weakness: an exact-match genre bubble in a thin catalog.** Genre is worth 2 of the 5 points, but it only counts if the song's genre label is spelled exactly the same as the user's. Meanwhile 13 of the 15 genres in the catalog have just one song. So for most listeners the system finds one "right" song and then falls off a 2-point cliff, and everything after it is ranked almost entirely by energy. That's why the rock fan's #2 pick is a pop gym anthem rather than the metal track, and why the pop fan never gets credit for *Rooftop Lights* ("indie pop" isn't "pop"). Lofi and pop fans get a well-matched list, while fans of every other genre get a single good match followed by a generic "songs at your energy level" list. In practice that list is the same handful of loud electronic tracks (*Gym Hero*, *Neon Euphoria*, *Storm Runner*) for anyone who likes high energy.

**Other limitations found while testing:**

- **No input checks.** An energy target of 1.5 is accepted. Quiet songs then get *negative* energy points, and scores stop being comparable between users.
- **Silent failure on unknown genres.** A "k-pop" fan gets no warning that their genre doesn't exist. Their best possible score is capped at 3 out of 5.
- **Energy works only one way.** It rewards closeness, but it's a single number. "Sad but high energy" can't be expressed, because the catalog's only sad song is quiet, and valence (how bright or dark a song sounds) is never scored.

---

## 7. Evaluation  

### Profiles tested

I ran six taste profiles through `python -m src.main` and read the top 5 for each. The full output is in the README under *Experiments You Tried*.

| Profile | Genre / mood / energy / sound | Purpose |
|---|---|---|
| High-Energy Pop | pop / happy / 0.8 / electronic | Normal listener |
| Chill Lofi | lofi / chill / 0.38 / acoustic | Normal listener |
| Deep Intense Rock | rock / intense / 0.9 / electronic | Normal listener |
| Sad but Hyped | folk / sad / 0.9 / electronic | Adversarial: genre and mood disagree with energy |
| Ghost Genre | k-pop / happy / 0.65 / electronic | Adversarial: genre not in catalog |
| Off the Scale | metal / aggressive / **1.5** / electronic | Adversarial: invalid energy target |

For each profile I asked two questions: does the #1 song make sense, and do the songs below it feel like "more of the same vibe"? Or are they just filler?

### Does it feel right? (High-Energy Pop)

Mostly yes. *Sunrise City* is first because it matches on everything: the right genre (+2), the right mood (+1), energy 0.82 against a target of 0.80 (+1.47), and a mostly electronic sound (+0.41), for 4.88 out of 5. Nothing else comes close because no other song is both pop *and* happy. The one result that feels wrong is #2.

**Why does *Gym Hero* keep showing up for people who just want happy pop?** In plain terms, the recommender gives points for being in the right *category* and for being at the right *intensity*. It doesn't care about the *feeling*. *Gym Hero* is filed under "pop", which alone is worth 2 points, the biggest single prize. It's also very energetic, so it's close to what a high-energy listener asked for. The fact that it's an aggressive workout track instead of a cheerful one only costs it the 1 mood point. Meanwhile *Rooftop Lights*, a genuinely happy song, is filed under "indie pop". The computer sees that as a completely different word from "pop", so it gets no genre points at all. Being in the right category beats having the right feeling. *Gym Hero* also shows up in 4 of the 6 lists overall: it's one of the most energetic and most electronic songs in the catalog, so anyone who wants loud, produced music gets it as filler.

### What surprised me

- **Sad but Hyped:** genre plus mood (3 points) easily beat energy. The user got a quiet folk ballad first, 0.60 away from the energy they asked for. Everything below it was loud songs with no sad mood at all. The system "solves" the conflict by obeying the labels and ignoring the energy.
- **Ghost Genre:** the system didn't break. It fell back to mood and energy and returned happy, mid-energy songs, which is sensible. But it never told the user it couldn't find k-pop.
- **Off the Scale:** the ranking came out identical to a target of 1.0, so the bad input didn't change *which* songs were picked. It only made the scores misleading, with some energy points going negative.
- **Experiment (energy ×2, genre ÷2):** it fixed the pop list (*Rooftop Lights* passed *Gym Hero*) but broke Sad but Hyped, where the only sad folk song dropped to #5. Rock and lofi didn't change at all. Overall the results got *different*, not better, so I kept the original weights.

### Comparing profiles, pair by pair

- **High-Energy Pop vs. Chill Lofi:** the two lists share no songs. Pop goes to bright, loud, produced tracks around 0.8 energy. Lofi goes to quiet, acoustic tracks around 0.4. Every part of the profile points the opposite way, so this is the easiest split for the system and the result is valid.
- **High-Energy Pop vs. Deep Intense Rock:** both want loud electronic music, so their lists overlap on *Gym Hero* and *Sunrise City*. The difference is in the middle of the list. For the rock fan, *Gym Hero* earns its #2 spot through mood ("intense"), and #3 is another loud track, *Neon Euphoria*. For the pop fan, *Gym Hero* gets #2 through genre instead, and the "happy" mood pulls *Rooftop Lights* in at #3. The mood setting is doing its job, deciding between songs of similar energy.
- **Chill Lofi vs. Deep Intense Rock:** opposite ends of the catalog with zero overlap. The rock list has nothing below 0.75 energy, and the lofi list has nothing above 0.42. This shows the energy-closeness rule really does pull lists toward the user's target rather than just "louder is better".
- **Deep Intense Rock vs. Sad but Hyped:** both target 0.9 energy with an electronic sound, so after #1 their lists are nearly the same: *Gym Hero*, *Neon Euphoria* and *Iron Tempest* appear in both. The big change is #1, *Storm Runner* for rock and *Paper Boats* for sad folk. For the sad folk fan, *Storm Runner* simply drops to #2. That makes sense, because genre and mood only matter for the one song that matches. After that, both users are just "people who like loud music".
- **High-Energy Pop vs. Ghost Genre:** both want happy music, and both get *Sunrise City* and *Rooftop Lights* at the top. For the k-pop fan the two tie at 2.66. Without the genre bonus, pop and indie pop are treated equally, and *Rooftop Lights* wins the tie because it's closer to their 0.65 energy target. This shows mood and energy carry the list when genre can't help.
- **Deep Intense Rock vs. Off the Scale (metal, energy 1.5):** both lists contain the same five loud songs, and each user's own genre takes #1 (*Storm Runner* for rock, *Iron Tempest* for metal). The invalid energy target didn't change the order, because asking for "1.5" ranks songs the same way as asking for "the loudest possible". It only lowered every score, which is why validating the input matters more for honest scores than for the ranking.

---

## 8. Future Work  


1. **Fuzzy genre and mood matching.** Give partial credit to related labels: "indie pop" for pop fans, "metal" for rock fans, "melancholic" for sad listeners. This would fix the biggest weakness I found.
2. **Validate input and say when something isn't found.** Keep the energy target between 0 and 1, and tell the user "no k-pop in the catalog, showing happy songs instead."
3. **Add valence and a variety rule.** Valence would separate bright songs from dark ones at the same energy. A variety rule (for example, at most one song per artist or genre in the top 5) would stop the same loud electronic tracks from filling every high-energy list.

---

## 9. Personal Reflection  


**Biggest learning moment.** The pop list put *Gym Hero*, an aggressive workout track, above *Rooftop Lights*, a happy indie-pop song. The rules were doing exactly what I told them. The problem was that "indie pop" and "pop" are different strings to a computer. A recommender can be "correct" and still feel wrong. Most of the bias came from the labels and the dataset, not the math.

**How AI helped, and when I double-checked it.** The AI assistant was fast at the mechanical parts: loading the CSV, writing the scoring function, formatting the terminal output, and generating stress-test profiles I wouldn't have thought of, like an energy target of 1.5. But I had to check its work:
- It first claimed genre outweighs mood plus energy combined. The numbers showed that was wrong, and we fixed it.
- Its first pair-by-pair comparisons said some lists were "nearly identical" when they weren't. I checked each claim against the real terminal output.
- When it undid the experiment with `git checkout`, it accidentally deleted an unsaved line of code and had to restore it.

The lesson: AI output sounds equally confident whether it's right or wrong, so I verified every number against an actual run.

**What surprised me.** Four simple rules and a sort already feel like a real recommender. The lofi list in particular looks like something a streaming app would show. Showing the reasons next to each song made it feel even more trustworthy, even though the logic is just addition. That also made me realize real apps can feel smart while hiding much simpler or more biased logic.

**What I'd try next.** Fuzzy genre matching first, then a variety rule so the top 5 isn't the same loud songs for everyone. After that, I'd try simulating a few users' play histories to see how collaborative filtering ("people like you also liked…") changes the results compared with this content-only approach.
