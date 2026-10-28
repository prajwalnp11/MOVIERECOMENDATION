import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

with open("movies.pkl", "rb") as f:
    production = pickle.load(f)

with open("similarity.pkl", "rb") as f:
    production_similarity = pickle.load(f)

indian = pd.read_csv("indian_movies_enriched.csv")

production = production.copy()
production["movie_id"] = pd.to_numeric(
    production["movie_id"], errors="coerce"
)
indian["movie_id"] = pd.to_numeric(
    indian["movie_id"], errors="coerce"
)

production = production.dropna(subset=["movie_id", "title"])
indian = indian.dropna(subset=["movie_id", "title"])

production["movie_id"] = production["movie_id"].astype(int)
indian["movie_id"] = indian["movie_id"].astype(int)

production_ids = set(production["movie_id"])
indian = indian.loc[
    ~indian["movie_id"].isin(production_ids)
].copy()

indian["tags"] = (
    indian["title"].fillna("").astype(str) + " " +
    indian["overview"].fillna("").astype(str) + " " +
    indian["genres"].fillna("").astype(str) + " " +
    indian["keywords"].fillna("").astype(str) + " " +
    indian["cast"].fillna("").astype(str) + " " +
    indian["directors"].fillna("").astype(str)
).str.lower()

production_tags = production["tags"].fillna("").astype(str)

production["movie_id"] = production["movie_id"].astype(int)
indian["movie_id"] = indian["movie_id"].astype(int)

production_for_model = production[["movie_id", "title", "tags"]].copy()
indian_for_model = indian[["movie_id", "title", "tags"]].copy()

combined = pd.concat(
    [production_for_model, indian_for_model],
    ignore_index=True
)

combined["tags"] = combined["tags"].fillna("").astype(str)
combined = combined.drop_duplicates(subset="movie_id")
combined.reset_index(drop=True, inplace=True)

vectorizer = TfidfVectorizer(
    max_features=20000,
    stop_words="english",
    ngram_range=(1, 2),
    sublinear_tf=True,
)

matrix = vectorizer.fit_transform(combined["tags"])
similarity = cosine_similarity(matrix, dense_output=True)

with open("movies_indian_candidate.pkl", "wb") as f:
    pickle.dump(combined, f)

with open("similarity_indian_candidate.pkl", "wb") as f:
    pickle.dump(similarity, f)

with open("tfidf_indian_candidate.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("\nCandidate model built successfully.")
print("Original production movies:", len(production))
print("Unique Indian movies added:", len(indian))
print("Total candidate movies:", len(combined))
print("Similarity matrix shape:", similarity.shape)
print("Similarity values finite:", bool(pd.notna(similarity).all()))
print("Production similarity shape:", production_similarity.shape)
print("Production files were not modified.")

print("\nNew movies by language:")
print(indian["language_name"].value_counts().to_string())

print("\nSample Kannada movies:")
print(
    indian.loc[
        indian["language_name"].eq("Kannada"), "title"
    ].head(15).to_string(index=False)
)
