
import streamlit as st
import pickle

# Load saved movie data
with open("movies.pkl", "rb") as f:
    movies = pickle.load(f)

with open("similarity.pkl", "rb") as f:
    similarity = pickle.load(f)

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Movie Recommendation System")
st.write("Find your next favourite movie!")

movie_titles = movies["title"].tolist()

selected_movie = st.selectbox(
    "Select a movie",
    movie_titles
)

if st.button("Recommend Movies"):
    movie_index = movies.index[
        movies["title"] == selected_movie
    ][0]

    distances = similarity[movie_index]

    recommendations = sorted(
        enumerate(distances),
        key=lambda item: item[1],
        reverse=True
    )[1:6]

    st.subheader("Recommended Movies")

    for index, score in recommendations:
        st.write(f"🍿 {movies.iloc[index]['title']}")
        st.caption(f"Similarity score: {score:.3f}")
