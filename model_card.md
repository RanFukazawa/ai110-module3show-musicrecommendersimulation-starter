# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **EchoMatch 1.0**  

---

## 2. Intended Use  

EchoMatch suggests songs from a small catalog based on a listener's stated
genre, mood, energy, and acoustic preferences. It assumes the user can
describe their taste in simple terms up front, rather than learning from
listening history like real streaming apps do. This is a classroom
simulation, not a production recommender — it is meant to demonstrate how
content-based filtering works, not to serve real listeners.

**Not intended for:** real user-facing recommendations, large catalogs, or
any use where an exact-match genre/mood label is unlikely to exist for
every possible taste.

---

## 3. How the Model Works  

Each song gets a score based on how well it matches the user's stated
taste. A matching genre is worth the most points, a matching mood is worth
half as much, and how close the song's energy is to the user's preferred
energy fills in the rest — closer energy means more points, not just
"higher energy is better." A small bonus or penalty is added depending on
whether the song is acoustic and whether the user likes that. All the
songs get scored this way, then they are sorted from highest to lowest and
the top few are shown, along with a plain-language reason for each one.

---

## 4. Data  

The catalog has 18 songs I expanded from an original set of 10, adding new
genres (hip-hop, classical, EDM, folk, R&B, metal, country, reggae) and
moods (melancholic, euphoric, aggressive, nostalgic, sultry) that weren't
represented before. Each song has a genre, mood, and four numeric features
(energy, tempo, valence, danceability, acousticness) on a 0–1 scale. 13 of
the 15 genres have only one song each, so there is very little variety
within most genres. The dataset has no lyrics, artist popularity, or
listening history — only these labeled attributes.

---

## 5. Strengths  

The system clearly separates very different tastes — a "chill lofi" profile
and a "high-energy pop" profile get completely different top results, which
shows the scoring is actually responding to the input, not just returning
the same songs every time. It handles missing or nonsense input (a genre
that does not exist, a profile with only one field filled in) without
crashing, falling back sensibly to whatever signals are available. The
reason strings make it easy to see exactly why a song ranked where it did,
which matches the "explainable" goal better than a black-box score would.

---

## 6. Limitations and Bias 

The most significant remaining bias is a "genre monopoly" effect: 13 of the
catalog's 15 genres contain exactly one song each, so a user's favorite
genre almost always wins the genre bonus with zero competition, regardless
of how well that song's mood or energy actually fit the rest of their
profile. This is not a scoring flaw so much as a dataset-size limitation,
but it means most genre-based recommendations are really "the only
option," not a genuine ranking. During evaluation I also found that
acousticness used a flat threshold while energy used a continuous,
distance-based formula — I fixed this by scaling the acoustic
bonus/penalty continuously too, so a song's exact acousticness now
matters rather than just whether it crosses a cutoff.

---

## 7. Evaluation

I tested six user profiles: three normal tastes (High-Energy Pop, Chill
Lofi, Deep Intense Rock) and three adversarial ones (Contradictory Taste,
Nonexistent Genre, Missing Keys), to check both accuracy and robustness.

**High-Energy Pop vs. Deep Intense Rock** — each profile got a genuinely
different #1 song (Sunrise City vs. Storm Runner), confirming the system
reads the actual input rather than defaulting to one answer.

**High-Energy Pop vs. Chill Lofi** — results flipped completely between
loud/electronic and quiet/acoustic picks, as expected. This also explains
why Gym Hero (pop, but "intense" not "happy") still ranks high for happy
profiles: energy is weighted almost as heavily as genre, so a strong
energy match can carry a song even when its mood doesn't fit.

**Contradictory Taste (the big surprise)** — a profile asking for "lofi"
genre but very high energy did not crash or break; it just let whichever
signal (energy, mood) was strongest for each song win out, since lofi
songs were penalized for being acoustic. The system does not detect
contradictions, it just averages through them.

**Nonexistent Genre and Missing Keys** — both degraded gracefully:
an unknown genre zeroed out only the genre bonus and let other features
decide the ranking; missing fields simply skipped those scoring steps
rather than erroring out.

**Nonexistent Genre vs. Chill Lofi** — sharing the same mood and similar
energy, both profiles surfaced the same top songs (Library Rain, Midnight
Coding); Chill Lofi's just scored higher since it also earned the genre
bonus. This showed mood and energy pull real weight on their own, not
just genre.


```
Loading songs from data/songs.csv...
Loaded songs: 18

====================================================================================================
Profile: High-Energy Pop
User prefs: {'genre': 'pop', 'mood': 'happy', 'energy': 0.85, 'likes_acoustic': False}
====================================================================================================

Top Recommendations:

1. Sunrise City by Neon Echo  —  Score: 88.2% (4.85 / 5.5 pts)
   Because: genre match (pop) (+2.0 pts); mood match (happy) (+1.0 pt); very close energy match (+1.94 pts); more acoustic than you usually prefer (-0.09 pts)

2. Gym Hero by Max Pulse  —  Score: 69.3% (3.81 / 5.5 pts)
   Because: genre match (pop) (+2.0 pts); very close energy match (+1.84 pts)

3. Rooftop Lights by Indigo Parade  —  Score: 48.2% (2.65 / 5.5 pts)
   Because: mood match (happy) (+1.0 pt); very close energy match (+1.82 pts); more acoustic than you usually prefer (-0.17 pts)

4. Storm Runner by Voltline  —  Score: 33.3% (1.83 / 5.5 pts)
   Because: very close energy match (+1.88 pts)

5. Pulse Overdrive by Kinetic Wave  —  Score: 32.5% (1.79 / 5.5 pts)
   Because: very close energy match (+1.8 pts)

====================================================================================================
Profile: Chill Lofi
User prefs: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.3, 'likes_acoustic': True}
====================================================================================================

Top Recommendations:

1. Library Rain by Paper Lanterns  —  Score: 96.9% (5.33 / 5.5 pts)
   Because: genre match (lofi) (+2.0 pts); mood match (chill) (+1.0 pt); very close energy match (+1.9 pts); acoustic sound matches your preference (+0.43 pts)

2. Midnight Coding by LoRoom  —  Score: 92.9% (5.11 / 5.5 pts)
   Because: genre match (lofi) (+2.0 pts); mood match (chill) (+1.0 pt); very close energy match (+1.76 pts); acoustic sound matches your preference (+0.35 pts)

3. Focus Flow by LoRoom  —  Score: 76.2% (4.19 / 5.5 pts)
   Because: genre match (lofi) (+2.0 pts); very close energy match (+1.8 pts); acoustic sound matches your preference (+0.39 pts)

4. Spacewalk Thoughts by Orbit Bloom  —  Score: 62.2% (3.42 / 5.5 pts)
   Because: mood match (chill) (+1.0 pt); very close energy match (+1.96 pts); acoustic sound matches your preference (+0.46 pts)

5. Wandering Home by Sage & Willow  —  Score: 43.5% (2.39 / 5.5 pts)
   Because: very close energy match (+1.94 pts); acoustic sound matches your preference (+0.45 pts)

====================================================================================================
Profile: Deep Intense Rock
User prefs: {'genre': 'rock', 'mood': 'intense', 'energy': 0.9, 'likes_acoustic': False}
====================================================================================================

Top Recommendations:

1. Storm Runner by Voltline  —  Score: 89.6% (4.93 / 5.5 pts)
   Because: genre match (rock) (+2.0 pts); mood match (intense) (+1.0 pt); very close energy match (+1.98 pts)

2. Gym Hero by Max Pulse  —  Score: 52.9% (2.91 / 5.5 pts)
   Because: mood match (intense) (+1.0 pt); very close energy match (+1.94 pts)

3. Pulse Overdrive by Kinetic Wave  —  Score: 34.4% (1.89 / 5.5 pts)
   Because: very close energy match (+1.9 pts)

4. Iron Descent by Grave Machine  —  Score: 33.6% (1.85 / 5.5 pts)
   Because: very close energy match (+1.86 pts)

5. Sunrise City by Neon Echo  —  Score: 31.8% (1.75 / 5.5 pts)
   Because: very close energy match (+1.84 pts); more acoustic than you usually prefer (-0.09 pts)

====================================================================================================
Profile: Contradictory Taste (lofi + max energy)
User prefs: {'genre': 'lofi', 'mood': 'happy', 'energy': 0.95, 'likes_acoustic': False}
====================================================================================================

Top Recommendations:

1. Sunrise City by Neon Echo  —  Score: 48.2% (2.65 / 5.5 pts)
   Because: mood match (happy) (+1.0 pt); very close energy match (+1.74 pts); more acoustic than you usually prefer (-0.09 pts)

2. Midnight Coding by LoRoom  —  Score: 47.1% (2.59 / 5.5 pts)
   Because: genre match (lofi) (+2.0 pts); energy similarity (+0.94 pts); more acoustic than you usually prefer (-0.35 pts)

3. Focus Flow by LoRoom  —  Score: 45.6% (2.51 / 5.5 pts)
   Because: genre match (lofi) (+2.0 pts); energy similarity (+0.9 pts); more acoustic than you usually prefer (-0.39 pts)

4. Rooftop Lights by Indigo Parade  —  Score: 44.5% (2.45 / 5.5 pts)
   Because: mood match (happy) (+1.0 pt); very close energy match (+1.62 pts); more acoustic than you usually prefer (-0.17 pts)

5. Library Rain by Paper Lanterns  —  Score: 43.1% (2.37 / 5.5 pts)
   Because: genre match (lofi) (+2.0 pts); energy similarity (+0.8 pts); more acoustic than you usually prefer (-0.43 pts)

====================================================================================================
Profile: Nonexistent Genre
User prefs: {'genre': 'vaporwave', 'mood': 'chill', 'energy': 0.4, 'likes_acoustic': True}
====================================================================================================

Top Recommendations:

1. Library Rain by Paper Lanterns  —  Score: 60.5% (3.33 / 5.5 pts)
   Because: mood match (chill) (+1.0 pt); very close energy match (+1.9 pts); acoustic sound matches your preference (+0.43 pts)

2. Midnight Coding by LoRoom  —  Score: 60.2% (3.31 / 5.5 pts)
   Because: mood match (chill) (+1.0 pt); very close energy match (+1.96 pts); acoustic sound matches your preference (+0.35 pts)

3. Spacewalk Thoughts by Orbit Bloom  —  Score: 58.5% (3.22 / 5.5 pts)
   Because: mood match (chill) (+1.0 pt); very close energy match (+1.76 pts); acoustic sound matches your preference (+0.46 pts)

4. Coffee Shop Stories by Slow Stereo  —  Score: 43.5% (2.39 / 5.5 pts)
   Because: very close energy match (+1.94 pts); acoustic sound matches your preference (+0.45 pts)

5. Focus Flow by LoRoom  —  Score: 43.5% (2.39 / 5.5 pts)
   Because: very close energy match (+2.0 pts); acoustic sound matches your preference (+0.39 pts)

====================================================================================================
Profile: Missing Keys
User prefs: {'genre': 'pop'}
====================================================================================================

Top Recommendations:

1. Sunrise City by Neon Echo  —  Score: 36.4% (2.00 / 5.5 pts)
   Because: genre match (pop) (+2.0 pts)

2. Gym Hero by Max Pulse  —  Score: 36.4% (2.00 / 5.5 pts)
   Because: genre match (pop) (+2.0 pts)

3. Midnight Coding by LoRoom  —  Score: 0.0% (0.00 / 5.5 pts)
   Because: No strong matches found.

4. Storm Runner by Voltline  —  Score: 0.0% (0.00 / 5.5 pts)
   Because: No strong matches found.

5. Library Rain by Paper Lanterns  —  Score: 0.0% (0.00 / 5.5 pts)
   Because: No strong matches found.
```

---

## 8. Future Work  

- Add more songs per genre so genre matches actually compete against each
  other, instead of one song automatically "winning" by default.
- Let users express dislikes, not just likes (e.g. "avoid metal"), since
  right now an actively hated genre scores the same as a neutral one.
- Support fuzzy or adjacent genre matches (e.g. "pop" partially matching
  "indie pop") instead of exact-string-only matching.
---

## 9. Personal Reflection

My biggest learning moment was realizing a "more consistent" design is not
always better: normalizing every reason to a percentage made fixed
bonuses like the acoustic modifier show up as the same repeated number
on every song, hiding information instead of clarifying it, so I went
back to raw points for reasons while keeping percentages for the total.
AI tools sped up the boilerplate a lot, but I still had to double-check
anything involving judgment — a bug where `likes_acoustic` was typo'd as
`Likes_acoustic` never threw an error, it just silently did nothing, and
I only caught it by testing real outputs, not by reading the code.

What surprised me most was how "alive" a simple point system can feel —
a handful of if-statements and some arithmetic clearly told apart a happy
pop listener from a chill lofi listener, and even handled a
self-contradictory profile (lofi genre, high energy) in a reasonable way
without any learning or training data involved. If I extended this
project, I would fix the genre monopoly problem first (most genres have only
one song, so there's no real ranking happening), let users express
dislikes and not just preferences, and try adding a bit of real
collaborative filtering just to feel the difference from content-based
scoring firsthand. 
