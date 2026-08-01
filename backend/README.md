# Chatbot Backend

## Setup
1. Create virtual environment: `python -m venv venv`
2. Activate: `venv\Scripts\activate` (Windows)
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`

## Run Locally
`uvicorn main:app --reload`

## Run Tests
`pytest`

## Run Docker
`docker build -t chatbot-backend .`
`docker run -p 8000:8000 --env-file .env.example chatbot-backend`
