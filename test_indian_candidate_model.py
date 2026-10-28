import pickle
import numpy as np
import pandas as pd

with open("movies_indian_candidate.pkl", "rb") as f:
    movies = pickle.load(f)

with open("similarity_indian_candidate.pkl", "rb") as f:
    similarity = pickle.load(f)

print("Movie count:", len(movies))
print("Similarity shape:", similarity.shape)
print("All similarity values finite:", np.isfinite(similarity).all())
print("Duplicate movie IDs:", int(movies["movie_id"].duplicated().sum()))

title_to_index = {}
for idx, title in enumerate(movies["title"].astype(str)):
    title_to_index.setdefault(title.casefold(), idx)

def recommend(title, count=5):
    index = title_to_index.get(title.casefold())

    if index is None:
        print(f"\nMovie not found: {title}")
        return

    scores = similarity[index]
    indices = np.argsort(scores)[::-1]
    results = []

    for candidate_idx in indices:
        if candidate_idx == index:
            continue

        results.append((
            movies.iloc[candidate_idx]["title"],
            float(scores[candidate_idx])
        ))

        if len(results) == count:
            break

    print(f"\nRecommendations for: {title}")
    for name, score in results:
        print(f"  {name}: {score:.3f}")

for title in [
    "K.G.F: Chapter 1",
    "Kantara",
    "777 Charlie",
    "3 Idiots",
    "Drishyam",
    "Vikram",
]:
    recommend(title)

print("\nKannada-language metadata coverage:")
enriched = pd.read_csv("indian_movies_enriched.csv")
kn = enriched[enriched["language_name"] == "Kannada"]

print("Kannada movies:", len(kn))
print("With genres:", int(kn["genres"].fillna("").str.len().gt(0).sum()))
print("With overviews:", int(kn["overview"].fillna("").str.len().gt(0).sum()))
