import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TMDB_BEARER_TOKEN")

if not token:
    raise RuntimeError("TMDB_BEARER_TOKEN is missing from .env")

source_file = "indian_movies_discovered.csv"
output_file = "indian_movies_enriched.csv"

df = pd.read_csv(source_file)
df["movie_id"] = pd.to_numeric(df["movie_id"], errors="coerce")
df = df.dropna(subset=["movie_id", "title"]).copy()
df["movie_id"] = df["movie_id"].astype(int)
df = df.drop_duplicates(subset="movie_id")

today = pd.Timestamp.now().normalize()
release_dates = pd.to_datetime(df["release_date"], errors="coerce")
df = df.loc[release_dates.notna() & (release_dates <= today)].copy()
df.reset_index(drop=True, inplace=True)

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {token}",
    "accept": "application/json",
})

genres_col = []
keywords_col = []
cast_col = []
director_col = []
overview_col = []
status_col = []

for i, row in df.iterrows():
    movie_id = int(row["movie_id"])
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"

    try:
        response = session.get(
            url,
            params={
                "language": "en-US",
                "append_to_response": "keywords,credits",
            },
            timeout=20,
        )

        if response.status_code == 429:
            print("TMDB rate limit reached. Stopping safely.")
            raise SystemExit(1)

        response.raise_for_status()
        details = response.json()

        genres = [
            item["name"] for item in details.get("genres", [])
        ]

        keyword_data = details.get("keywords", {})
        keywords = keyword_data.get(
            "keywords",
            keyword_data.get("results", [])
        )
        keywords = [
            item["name"] for item in keywords
        ]

        credits = details.get("credits", {})
        cast = [
            item["name"]
            for item in credits.get("cast", [])[:5]
        ]

        directors = [
            item["name"]
            for item in credits.get("crew", [])
            if item.get("job") == "Director"
        ]

        genres_col.append(", ".join(genres))
        keywords_col.append(", ".join(keywords))
        cast_col.append(", ".join(cast))
        director_col.append(", ".join(directors))
        overview_col.append(
            details.get("overview") or row.get("overview") or ""
        )
        status_col.append(details.get("status") or "")

    except requests.RequestException as error:
        print(f"Failed movie {movie_id}: {error}")
        genres_col.append("")
        keywords_col.append("")
        cast_col.append("")
        director_col.append("")
        overview_col.append(row.get("overview") or "")
        status_col.append("Fetch failed")

    if (len(genres_col) % 25) == 0:
        print(f"Processed {len(genres_col)}/{len(df)} movies")

    time.sleep(0.15)

df["genres"] = genres_col
df["keywords"] = keywords_col
df["cast"] = cast_col
df["directors"] = director_col
df["overview"] = overview_col
df["tmdb_status"] = status_col

df.to_csv(output_file, index=False)

print("\nEnrichment complete.")
print("Movies:", len(df))
print("Languages:", df["language_name"].nunique())
print("Rows with genres:", int(df["genres"].fillna("").str.len().gt(0).sum()))
print("Rows with overviews:", int(df["overview"].fillna("").str.len().gt(0).sum()))
print("Rows with fetch failures:", int(df["tmdb_status"].eq("Fetch failed").sum()))
print("Output:", output_file)

print("\nMovies per language:")
print(df["language_name"].value_counts().to_string())
