import os
import time
import pickle
import requests
import pandas as pd
import numpy as np

from dotenv import load_dotenv
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()
TOKEN = os.getenv("TMDB_BEARER_TOKEN")

if not TOKEN:
    raise RuntimeError("TMDB_BEARER_TOKEN is missing from .env")

BASE = "https://api.themoviedb.org/3"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "accept": "application/json",
}

session = requests.Session()
session.headers.update(HEADERS)

# Load existing production data read-only.
with open("movies.pkl", "rb") as f:
    existing = pickle.load(f)

existing = existing[["movie_id", "title", "tags"]].copy()
existing["movie_id"] = pd.to_numeric(
    existing["movie_id"], errors="coerce"
)
existing = existing.dropna(subset=["movie_id"])
existing["movie_id"] = existing["movie_id"].astype("int64")
existing["title"] = existing["title"].fillna("").astype(str)
existing["tags"] = existing["tags"].fillna("").astype(str)

# Load the persistent catalogue so movies remain available after leaving
# TMDB's popular list.
collected = pd.read_csv("tmdb_movie_catalog.csv")
collected["id"] = pd.to_numeric(collected["id"], errors="coerce")
collected = collected.dropna(subset=["id", "title"]).copy()
collected["id"] = collected["id"].astype("int64")
collected = collected.drop_duplicates("id", keep="last")

existing_ids = set(existing["movie_id"])
new_rows = collected[~collected["id"].isin(existing_ids)].copy()

# Reuse previously enriched records instead of fetching their metadata again.
enriched_path = "new_movies_candidate.csv"
if os.path.exists(enriched_path):
    previous = pd.read_csv(enriched_path)
    if {"movie_id", "title", "tags"}.issubset(previous.columns):
        previous["movie_id"] = pd.to_numeric(
            previous["movie_id"], errors="coerce"
        )
        previous = previous.dropna(subset=["movie_id"]).copy()
        previous["movie_id"] = previous["movie_id"].astype("int64")
        previous = previous.drop_duplicates("movie_id", keep="last")
    else:
        previous = pd.DataFrame(
            columns=["movie_id", "title", "tags", "genres", "release_date"]
        )
else:
    previous = pd.DataFrame(
        columns=["movie_id", "title", "tags", "genres", "release_date"]
    )

catalog_new_ids = set(new_rows["id"])
reusable = previous[previous["movie_id"].isin(catalog_new_ids)].copy()
reusable_ids = set(reusable["movie_id"])
to_enrich = new_rows[~new_rows["id"].isin(reusable_ids)].copy()

print("Existing production rows:", len(existing))
print("Persistent catalogue movies:", len(collected))
print("New IDs outside production:", len(new_rows))
print("Previously enriched records reusable:", len(reusable))
print("New records requiring enrichment:", len(to_enrich))

def get_json(url, params=None):
    response = session.get(url, params=params, timeout=30)
    if response.status_code == 429:
        raise RuntimeError("TMDB rate limit reached; wait and retry.")
    response.raise_for_status()
    return response.json()

def make_tags(movie_id, fallback_title, fallback_overview):
    details = get_json(
        f"{BASE}/movie/{movie_id}",
        {"language": "en-US"},
    )

    genres = [
        item.get("name", "")
        for item in details.get("genres", [])
    ]

    keywords_data = get_json(f"{BASE}/movie/{movie_id}/keywords")
    keywords = [
        item.get("name", "")
        for item in keywords_data.get("keywords", [])
    ]

    credits = get_json(f"{BASE}/movie/{movie_id}/credits")
    cast = [
        person.get("name", "")
        for person in credits.get("cast", [])[:5]
    ]

    directors = [
        person.get("name", "")
        for person in credits.get("crew", [])
        if person.get("job") == "Director"
    ]

    title = details.get("title") or fallback_title
    overview = details.get("overview") or fallback_overview or ""

    # Keep source information in separate fields too.
    tags = " ".join(
        [title, overview]
        + genres
        + keywords
        + cast
        + directors
    )

    return {
        "movie_id": int(movie_id),
        "title": title,
        "tags": tags,
        "genres": ", ".join(genres),
        "release_date": details.get("release_date", ""),
    }

new_records = []
failures = []

for number, row in enumerate(to_enrich.to_dict("records"), start=1):
    movie_id = int(row["id"])
    try:
        new_records.append(
            make_tags(
                movie_id,
                str(row.get("title", "")),
                str(row.get("overview", "")),
            )
        )
        print(f"[{number}/{len(to_enrich)}] OK: {row.get('title', movie_id)}")
    except Exception as error:
        failures.append((movie_id, str(row.get("title", "")), str(error)))
        print(f"[{number}/{len(to_enrich)}] FAILED ID {movie_id}: {error}")

    time.sleep(0.15)

new_df = pd.DataFrame(
    new_records,
    columns=["movie_id", "title", "tags", "genres", "release_date"],
)

# Combine reusable metadata with newly fetched metadata.
new_df = pd.concat([reusable, new_df], ignore_index=True, sort=False)
new_df = new_df.drop_duplicates("movie_id", keep="last")

# Do not publish a partial candidate if any required metadata request failed.
if failures:
    raise RuntimeError(
        f"Candidate build aborted: {len(failures)} metadata requests failed. "
        "Existing candidate artifacts were not intentionally overwritten."
    )

expected_ids = set(new_rows["id"])
enriched_ids = set(new_df["movie_id"])
missing_ids = expected_ids - enriched_ids
if missing_ids:
    raise RuntimeError(
        f"Candidate build aborted: {len(missing_ids)} catalogue movies "
        "are still missing enrichment."
    )

# Combine without changing original movie tags.
candidate = pd.concat(
    [
        existing[["movie_id", "title", "tags"]],
        new_df[["movie_id", "title", "tags"]],
    ],
    ignore_index=True,
)

candidate["tags"] = candidate["tags"].fillna("").astype(str)

print("\nBuilding candidate text features...")
vectorizer = CountVectorizer(
    max_features=5000,
    stop_words="english",
)
features = vectorizer.fit_transform(candidate["tags"])
similarity = cosine_similarity(features)

# Write candidate files only; production files stay untouched.
candidate.to_pickle("movies_candidate.pkl")
with open("similarity_candidate.pkl", "wb") as f:
    pickle.dump(similarity, f, protocol=pickle.HIGHEST_PROTOCOL)

new_df.to_csv("new_movies_candidate.csv", index=False)

with open("candidate_build_report.txt", "w") as f:
    f.write(f"Existing movies: {len(existing)}\n")
    f.write(f"Collected unique movies: {len(collected)}\n")
    f.write(f"New movie records enriched: {len(new_df)}\n")
    f.write(f"Failed records: {len(failures)}\n")
    f.write(f"Candidate dataset rows: {len(candidate)}\n")
    f.write(f"Feature matrix shape: {features.shape}\n")
    f.write(f"Similarity matrix shape: {similarity.shape}\n")
    f.write("\nFailures:\n")
    for movie_id, title, error in failures:
        f.write(f"{movie_id} | {title} | {error}\n")

print("\nCandidate build finished.")
print("Candidate movies:", len(candidate))
print("New movies enriched:", len(new_df))
print("Failed enrichment requests:", len(failures))
print("Candidate similarity shape:", similarity.shape)
print("Files created:")
print("  movies_candidate.pkl")
print("  similarity_candidate.pkl")
print("  new_movies_candidate.csv")
print("  candidate_build_report.txt")
