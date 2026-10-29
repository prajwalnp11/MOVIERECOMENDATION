# Movie Recommendation System

A content-based movie recommendation web application built with Python, pandas, and scikit-learn. Users can select a movie and discover similar titles, with movie posters retrieved from The Movie Database (TMDB).

**Live Demo:** https://movierecomendation-6tuyoqvqh9zotgqwsblyka.streamlit.app/

## Features

- Select a movie from the available movie collection.
- Get recommendations based on movie similarity.
- View movie posters using TMDB.
- Explore recommendations for different selected movies.
- Access the application through a public web link.

## Tech Stack

- **Language:** Python
- **Web framework:** Streamlit
- **Data processing:** pandas
- **Machine learning:** scikit-learn
- **Movie metadata and posters:** TMDB API
- **Model and data storage:** Pickle
- **Large-file versioning:** Git LFS
- **Deployment:** Streamlit Community Cloud
- **Version control:** Git and GitHub

## Model Optimization

The movie similarity matrix was converted from `float64` to `float32` to reduce storage and memory requirements.

The matrix size decreased from approximately 260 MB to 130 MB, a reduction of about 50%. Top-10 recommendation rankings matched for the six sampled movie rows tested during validation.

## Live Testing

The deployed application was tested for:

- Homepage loading
- Movie selection
- Recommendation logic
- Poster loading
- Recommendations across different selections
- Public access
- Refresh behavior

All seven checks passed during manual testing.

## Run Locally

### 1. Clone the repository

```bash
git clone https://github.com/prajwalnp11/MOVIERECOMENDATION.git
cd MOVIERECOMENDATION
```

### 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the TMDB token

Create a `.env` file in the project directory:

```env
TMDB_BEARER_TOKEN=your_tmdb_bearer_token
```

Replace the placeholder with your own token. Never commit `.env` or expose API credentials publicly.

Ensure the application loads the token from the environment and that the required model and movie data files are available locally.

### 5. Start the application

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit in your browser.

## Project Structure

The main files include:

- `app.py` — Streamlit application
- `requirements.txt` — Python dependencies
- `movies_indian_candidate.pkl` — Movie dataset used by the application
- `similarity_indian_candidate_f32.pkl` — Optimized similarity matrix
- `.gitattributes` — Git LFS tracking configuration

## Future Improvements

- Add search and genre-based filtering.
- Display ratings, release dates, and movie descriptions.
- Improve recommendation evaluation using a larger test set.
- Add automated tests and continuous integration.
- Monitor startup time, memory usage, and deployment reliability.

## Disclaimer

This is an educational and portfolio project. Movie metadata and posters are provided through TMDB. This project is not affiliated with or endorsed by TMDB.
