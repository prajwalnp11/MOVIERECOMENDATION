import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("TMDB_BEARER_TOKEN")

if not token:
    raise RuntimeError("TMDB_BEARER_TOKEN is missing from .env")

languages = {
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "bn": "Bengali",
    "mr": "Marathi",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "as": "Assamese",
    "or": "Odia",
    "ur": "Urdu",
}

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {token}",
    "accept": "application/json",
})

all_movies = []
max_pages_per_language = 5

for code, language_name in languages.items():
    print(f"\nDiscovering {language_name} movies...")

    for page in range(1, max_pages_per_language + 1):
        try:
            response = session.get(
                "https://api.themoviedb.org/3/discover/movie",
                params={
                    "with_original_language": code,
                    "language": "en-US",
                    "sort_by": "popularity.desc",
                    "include_adult": "false",
                    "include_video": "false",
                    "page": page,
                },
                timeout=20,
            )

            if response.status_code == 429:
                print("Rate limit reached. Stopping safely.")
                raise SystemExit(1)

            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])

            for movie in results:
                all_movies.append({
                    "movie_id": movie.get("id"),
                    "title": movie.get("title"),
                    "original_title": movie.get("original_title"),
                    "original_language": movie.get("original_language"),
                    "language_name": language_name,
                    "release_date": movie.get("release_date"),
                    "overview": movie.get("overview"),
                    "popularity": movie.get("popularity"),
                    "vote_average": movie.get("vote_average"),
                    "poster_path": movie.get("poster_path"),
                })

            print(f"  Page {page}: {len(results)} movies")

            if page >= data.get("total_pages", 0):
                break

            time.sleep(0.25)

        except requests.RequestException as error:
            print(f"Request failed for {language_name}, page {page}: {error}")
            break

df = pd.DataFrame(all_movies)

if not df.empty:
    df = df.drop_duplicates(subset="movie_id")
    df.to_csv("indian_movies_discovered.csv", index=False)

print("\nDiscovery complete.")
print("Unique movies:", len(df))
print("Saved to: indian_movies_discovered.csv")

if not df.empty:
    print("\nMovies by original language:")
    print(df["language_name"].value_counts().to_string())

    print("\nSample titles:")
    print(
        df[["title", "language_name", "release_date"]]
        .head(30)
        .to_string(index=False)
    )
