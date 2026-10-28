import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv

# Project paths
BASE_DIR = Path(__file__).resolve().parent
HISTORY_DIR = BASE_DIR / "tmdb_history"
LATEST_FILE = BASE_DIR / "tmdb_scheduled_latest.csv"
CATALOG_FILE = BASE_DIR / "tmdb_movie_catalog.csv"

# Load the private TMDB token from .env
load_dotenv(BASE_DIR / ".env")
token = os.getenv("TMDB_BEARER_TOKEN")

if not token:
    raise RuntimeError("TMDB_BEARER_TOKEN is missing from .env")

URL = "https://api.themoviedb.org/3/movie/popular"
HEADERS = {"Authorization": f"Bearer {token}"}
COLUMNS = [
    "id",
    "title",
    "release_date",
    "rating",
    "vote_count",
    "overview",
    "poster_path",
]


def atomic_save_csv(df, destination):
    """Write a CSV to a temporary file, then replace the destination."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        prefix=".tmdb_tmp_",
        suffix=".csv",
        dir=str(destination.parent),
    )
    os.close(fd)

    try:
        df.to_csv(temp_path, index=False)
        os.replace(temp_path, destination)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)



def update_catalog(df):
    """Merge collected movies into the persistent catalogue by TMDB ID."""
    incoming = df.copy()
    incoming["id"] = pd.to_numeric(incoming["id"], errors="coerce")
    incoming = incoming.dropna(subset=["id", "title"]).copy()
    incoming["id"] = incoming["id"].astype("int64")
    incoming = incoming.drop_duplicates(subset=["id"], keep="last")

    if CATALOG_FILE.exists():
        existing = pd.read_csv(CATALOG_FILE)
        if not {"id", "title"}.issubset(existing.columns):
            raise RuntimeError("Existing catalogue lacks required columns")

        existing["id"] = pd.to_numeric(existing["id"], errors="coerce")
        existing = existing.dropna(subset=["id", "title"]).copy()
        existing["id"] = existing["id"].astype("int64")

        combined = pd.concat(
            [existing, incoming], ignore_index=True, sort=False
        )
        combined = combined.drop_duplicates(subset=["id"], keep="last")
    else:
        combined = incoming

    combined = combined.sort_values("id").reset_index(drop=True)

    if combined.empty or combined["id"].duplicated().any():
        raise RuntimeError("Catalogue validation failed; catalogue not saved")

    if combined["title"].isna().any():
        raise RuntimeError("Catalogue has missing titles; catalogue not saved")

    atomic_save_csv(combined, CATALOG_FILE)
    print("Persistent catalogue:", CATALOG_FILE)
    print("Catalogue movies:", len(combined))
    print("Catalogue unique IDs:", combined["id"].nunique())


def main():
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    collected = []

    # Five pages, up to 20 movies per page
    with requests.Session() as session:
        session.headers.update(HEADERS)

        for page in range(1, 6):
            response = session.get(
                URL,
                params={"language": "en-US", "page": page},
                timeout=30,
            )
            response.raise_for_status()

            payload = response.json()
            results = payload.get("results", [])

            if not isinstance(results, list):
                raise RuntimeError(
                    f"Unexpected TMDB response on page {page}"
                )

            if not results:
                print(f"Page {page} returned no results; stopping.")
                break

            collected.extend(results)
            print(f"Page {page}: collected {len(results)} records")

    if not collected:
        raise RuntimeError(
            "TMDB returned no movies; existing CSV files were not updated"
        )

    df = pd.DataFrame(
        [
            {
                "id": movie.get("id"),
                "title": movie.get("title"),
                "release_date": movie.get("release_date"),
                "rating": movie.get("vote_average"),
                "vote_count": movie.get("vote_count"),
                "overview": movie.get("overview"),
                "poster_path": movie.get("poster_path"),
            }
            for movie in collected
        ],
        columns=COLUMNS,
    )

    # Reject invalid IDs and remove duplicate IDs
    df = df.dropna(subset=["id"])
    df = df[df["id"].astype(str).str.strip() != ""]
    df = df.drop_duplicates(subset=["id"], keep="first")

    if df.empty:
        raise RuntimeError("No valid movie IDs; output was not updated")

    # UTC timestamp for logs and the historical snapshot
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")
    history_file = HISTORY_DIR / f"tmdb_movies_{timestamp}.csv"

    # Save history first, then atomically replace the latest CSV
    atomic_save_csv(df, history_file)

    try:
        atomic_save_csv(df, LATEST_FILE)
    except Exception:
        # Preserve the history snapshot, but report that latest was not updated
        raise RuntimeError(
            f"History saved to {history_file}, but latest CSV update failed"
        )

    # Update the persistent catalogue only after latest collection succeeds.
    update_catalog(df)

    print("Collection time (UTC):", now.isoformat())
    print("Movies collected:", len(df))
    print("Duplicate IDs removed:", len(collected) - len(df))
    print("Latest file:", LATEST_FILE)
    print("History snapshot:", history_file)
    print("First five titles:")
    print(df["title"].head().to_string(index=False))


if __name__ == "__main__":
    main()