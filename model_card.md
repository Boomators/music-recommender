# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

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

Describe the dataset the model uses.  

Prompts:  

- How many songs are in the catalog  
- What genres or moods are represented  
- Did you add or remove data  
- Are there parts of musical taste missing in the dataset  

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
