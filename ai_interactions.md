# AI Interactions Log

> **Stretch features only.** Only fill in the sections that apply to stretch features you attempted. If you did not attempt a stretch feature, leave its section blank or delete it. This file is not required for the core project.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Implement all four optional stretch challenges in one agent session:
1. Add 5+ advanced song attributes and score them.
2. Add switchable scoring modes using a design pattern.
3. Add a diversity penalty for repeated artists and genres.
4. Add a readable summary table that includes the reasons.

The constraint was that the working "genre-first" recommender on `main` had to stay safe and produce unchanged results.

**Prompts used:**

I pasted the full stretch-challenge brief into Claude Code (agent mode) and let it plan the work. Key parts of the prompt:

> Introduce 5 or more complex attributes to your dataset that are not currently present in the baseline data, such as Song Popularity (0-100), Release Decade, or Detailed Mood Tags… Update both data/songs.csv and the scoring logic in src/recommender.py so scoring accounts for the new attributes.

> Build two or more different ranking strategies (e.g., "Genre-First," "Mood-First," or "Energy-Focused") so a user can switch between modes in main.py… brainstorm a design pattern (like a simple "Strategy" pattern) that keeps your code modular.

> Implement a "Diversity Penalty" that… penalize[s] a song's score if its artist is already present in the top recommendations list.

> …display your top recommendations [in a table]. Ensure… the table must include the "reasons" for each score.

**What did the agent generate or change?**

- **Git:** committed the previous phase on `main`, then created the `experiment/stretch-features` branch for all of this work.
- **`data/songs.csv`:** added `popularity`, `release_decade`, `mood_tags` (`|`-separated), `instrumentalness`, `explicit` for all 18 songs.
- **`src/recommender.py`:**
  - new optional fields on `Song` and `UserProfile`, with defaults so the existing tests still build them
  - a `ScoringMode` dataclass and three modes
  - scoring for tags, decade, popularity and instrumentalness
  - a `max_score()` helper
  - a greedy `diversify()` step
  - an explicit-content filter
  - `Recommender` now delegates to `recommend_songs`, so there's one code path
- **`src/main.py`:**
  - `argparse` flags `--mode`, `--diverse`, `--format table`, `--profile`, `-k`
  - two new profiles (Nostalgic Night Owl, Clean Workout)
  - an ASCII table renderer with no dependencies
- **`tests/test_recommender.py`:** 5 new tests: CSV parsing, partial tag credit, mood-first ordering, explicit filtering, unique artists under `--diverse`.
- **Commands run:** `python -m src.main` with every mode and flag, a `diff` against the saved baseline output, and `pytest` (7 passed).

**What did you verify or fix manually?**

- **No regression:** the output for the original six profiles in genre-first mode was diffed against the saved pre-change output and is byte-identical. New preferences only score when a profile sets them.
- **Bug caught by testing:** explicit lyrics were first a −1.0 penalty. The Clean Workout run showed *Gym Hero* (explicit) still at **#1** with 4.93 vs. 3.79, because one penalty can't cancel out a song that matches on everything else. It was changed to a hard filter and a test was added.
- **Score math:** checked the partial tag credit by hand. 1 of 2 tags matched should give half of the 1.0 tag weight, plus 1.5 energy and 0.5 electronic, for 2.5 total. That's the value the test asserts.
- **Diversity:** checked by reading the reasons column. Penalties show up as "artist already listed (-1.00)", and High-Energy Pop no longer lists two Neon Echo songs.
- **Data:** the new values (popularity, decades, tags) were invented by the AI. I should sanity-check them against my own sense of each song before trusting conclusions drawn from them.
- **Tool friction:** one file write was refused because the file had changed on disk since the agent last read it. The agent re-read it and retried.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

**Strategy pattern**, in its lightweight "configuration object" form. Each ranking strategy is a frozen `ScoringMode` dataclass that holds one set of weights. The same `score_song` algorithm runs with whichever strategy is passed in.

**How did AI help you brainstorm or implement it?**

We weighed two versions of Strategy:
1. **A separate scoring function or class per mode** (`GenreFirstScorer.score()`, `MoodFirstScorer.score()`, …). This is the textbook version, flexible enough for modes that use different *logic*. But all three modes would repeat the same genre/mood/energy/tag rules, and only the numbers would change.
2. **One algorithm with swappable weight objects.** The modes in this assignment differ only in *how much* each signal counts, not *which* signals exist, so this removes the duplication. Adding a mode is one line. It's also easy to compare modes side by side in a table.

We chose option 2. The trade-off: a future mode that needs genuinely different logic (for example, collaborative filtering) would need option 1. The `mode` parameter is already where a strategy gets passed in, though, so upgrading later wouldn't change the callers.

**How does the pattern appear in your final code?**

- `ScoringMode` dataclass and the `GENRE_FIRST`, `MOOD_FIRST` and `ENERGY_FOCUSED` instances, plus the `MODES` registry: top of `src/recommender.py`
- `score_song(user_prefs, song, mode)` reads every weight from `mode` (`mode.genre`, `mode.tags`, …)
- `recommend_songs(..., mode=...)` and `Recommender.recommend(..., mode=...)` pass the strategy through
- `max_score(user_prefs, mode)` computes the "out of" value for each strategy
- `src/main.py`: `--mode` chooses from `MODES` by name
