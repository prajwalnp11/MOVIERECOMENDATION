# Movie Recommendation System — DevOps Project

A movie recommendation web application built with Python and Streamlit, containerized using Docker, and deployed locally to Kubernetes. GitHub Actions automatically builds and publishes multi-platform Docker images to Docker Hub.

## Features

- Movie recommendations using a precomputed similarity model
- Python and Streamlit web interface
- Docker containerization
- Kubernetes Deployment and Service
- Kubernetes Secret for API-key configuration
- Readiness and liveness health probes
- CPU and memory resource requests and limits
- Automated multi-platform Docker builds using GitHub Actions
- Docker Hub image publishing for `linux/amd64` and `linux/arm64`

## Technology Stack

- Python
- Streamlit
- Pandas and scikit-learn
- Docker
- Kubernetes
- Git and GitHub
- GitHub Actions
- Docker Hub
- Git LFS for the large similarity model

## Architecture

1. The user interacts with the Streamlit application.
2. Python loads the movie dataset and precomputed similarity model.
3. Docker packages the application and its dependencies into an image.
4. GitHub Actions builds and publishes Docker images when changes are pushed to `main`.
5. Kubernetes runs the application in a container and manages its availability.
6. Kubernetes Secrets provide the TMDB API key without storing it in the Deployment manifest.

## Project Structure

```text
movie-recommender/
├── .github/workflows/
│   └── docker-ci-cd.yml
├── app.py
├── movies.pkl
├── similarity.pkl
├── requirements.txt
├── Dockerfile
├── deployment.yaml
├── .dockerignore
├── .gitignore
└── README.md
```

## Run Locally with Python

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file in the project root and add your own TMDB API key:

```text
TMDB_API_KEY=your_tmdb_api_key
```

Never commit the real `.env` file or publish API keys.

Run the application:

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

## Run with Docker

Build the image:

```bash
docker build -t movie-recommender:local .
```

Run the container:

```bash
docker run --rm -p 8501:8501 --env-file .env movie-recommender:local
```

Open `http://localhost:8501`.

## Docker Hub

Published image repository:

https://hub.docker.com/r/prajwalnp11/movie-recommender

Pull the latest image:

```bash
docker pull prajwalnp11/movie-recommender:latest
```

Run it with your local environment file:

```bash
docker run --rm -p 8501:8501 --env-file .env prajwalnp11/movie-recommender:latest
```

## Kubernetes Deployment

Prerequisites: Docker Desktop with Kubernetes enabled, `kubectl`, and a valid local `.env` file.

Create the Kubernetes Secret if it does not already exist:

```bash
kubectl create secret generic movie-recommender-secret --from-env-file=.env
```

Apply the Deployment and Service manifests:

```bash
kubectl apply -f deployment.yaml
kubectl get service movie-recommender-service || kubectl expose deployment movie-recommender --type=NodePort --port=8501 --target-port=8501 --name=movie-recommender-service
```

Check deployment status:

```bash
kubectl get deployments
kubectl get pods
kubectl get services
kubectl rollout status deployment/movie-recommender
```

If your Service is named `movie-recommender-service`, access the app using port forwarding:

```bash
kubectl port-forward service/movie-recommender-service 8502:8501
```

Open `http://localhost:8502`.

Stop port forwarding with `Ctrl+C`.

## CI/CD Pipeline

The GitHub Actions workflow in `.github/workflows/docker-ci-cd.yml`:

1. Checks out the source code, including Git LFS files.
2. Sets up QEMU and Docker Buildx.
3. Authenticates with Docker Hub using GitHub Actions secrets.
4. Builds images for `linux/amd64` and `linux/arm64`.
5. Publishes the `latest` tag and a commit-SHA tag to Docker Hub.

Required GitHub repository secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

Do not put credentials directly in the workflow file.

## Kubernetes Reliability

The Deployment includes:

- Readiness and liveness probes using Streamlit's `/_stcore/health` endpoint
- CPU requests and limits
- Memory requests and limits
- A Kubernetes Secret reference for the TMDB API key

## Troubleshooting

**Check application logs:**

```bash
kubectl logs deployment/movie-recommender
```

**Check recent Kubernetes events:**

```bash
kubectl get events --sort-by=.metadata.creationTimestamp
```

**Check rollout status:**

```bash
kubectl rollout status deployment/movie-recommender
```

**Check Docker images:**

```bash
docker images
```

## Future Improvements

- Add automated application tests to the CI pipeline.
- Add image vulnerability scanning.
- Add monitoring and resource metrics.
- Add a staging environment and deployment approval steps.
- Improve deployment automation and version management.

## Author

**Prajwal N P**

GitHub: [Prajwal N P](https://github.com/prajwalnp11)
