
import os
import pickle

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_API_URL = "https://api.themoviedb.org/3/movie/"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)


# Load saved movie data and similarity matrix
@st.cache_resource
def load_data():
    with open("movies.pkl", "rb") as file:
        movies_data = pickle.load(file)

    with open("similarity.pkl", "rb") as file:
        similarity_data = pickle.load(file)

    return movies_data, similarity_data


movies, similarity = load_data()


# Fetch poster from TMDB using the movie ID
@st.cache_data(show_spinner=False)
def get_poster(movie_id, api_key):
    if not api_key:
        return None

    try:
        response = requests.get(
            f"{TMDB_API_URL}{int(movie_id)}",
            params={"api_key": api_key},
            timeout=10
        )

        if response.status_code != 200:
            return None

        poster_path = response.json().get("poster_path")

        if poster_path:
            return POSTER_BASE_URL + poster_path

    except (requests.RequestException, ValueError, TypeError):
        return None

    return None


# Display a movie poster or a fallback message
def show_movie(movie_row, title, score=None):
    st.markdown(f"**{title}**")

    poster_url = get_poster(movie_row["movie_id"], TMDB_API_KEY)

    if poster_url:
        st.image(poster_url, use_container_width=True)
    else:
        st.info("Poster unavailable")

    if score is not None:
        st.caption(f"Similarity score: {score:.3f}")


# App interface
st.title("🎬 Movie Recommendation System")
st.write("Find your next favourite movie!")

if not TMDB_API_KEY:
    st.warning(
        "TMDB API key not found. Check that your .env file "
        "contains TMDB_API_KEY=your_key"
    )

movie_titles = movies["title"].tolist()

selected_movie = st.selectbox(
    "Select a movie",
    movie_titles
)

if st.button("Recommend Movies", type="primary"):
    movie_index = movies.index[
        movies["title"] == selected_movie
    ][0]

    selected_row = movies.iloc[movie_index]

    distances = similarity[movie_index]

    recommendations = sorted(
        enumerate(distances),
        key=lambda item: item[1],
        reverse=True
    )[1:6]

    st.subheader("🎥 Selected Movie")

    selected_col, details_col = st.columns([1, 3])

    with selected_col:
        show_movie(selected_row, selected_movie)

    with details_col:
        st.write(f"**Movie:** {selected_movie}")
        st.write("Here are five movies recommended for you.")

    st.divider()
    st.subheader("🍿 Recommended Movies")

    columns = st.columns(5)

    for column, (index, score) in zip(columns, recommendations):
        with column:
            recommended_row = movies.iloc[index]
            show_movie(
                recommended_row,
                recommended_row["title"],
                score
            )

st.divider()

st.caption(
    "This product uses the TMDB APIs but is not endorsed, "
    "certified, or otherwise approved by TMDB."
)
st.markdown("[TMDB](https://www.themoviedb.org/)")
