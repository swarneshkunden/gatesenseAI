# GatesenseAI

![CI](https://github.com/your-username/your-repo-name/actions/workflows/ci.yml/badge.svg)

GatesenseAI is a full-stack stadium operations assistant built for a FIFA World Cup 2026-style event environment. It combines a React + Vite frontend with a FastAPI backend to help volunteers manage crowd flow, translate fan requests, generate broadcast announcements, and simulate stadium data.

## Project Overview

### What the app does
- Shows live crowd density information for stadium zones
- Provides AI-assisted operational recommendations for crowd bottlenecks
- Helps translate fan messages into English and back into a target language
- Generates megaphone-style broadcast scripts for volunteers
- Lets users upload CSV simulation data to test different scenarios

### Tech stack
- Frontend: React, TypeScript, Vite, Lucide icons
- Backend: Python, FastAPI, Uvicorn
- AI integration: Google Gemini API (optional, with mock fallback)
- Data handling: pandas, pydantic, python-multipart

## Project Structure

- src/ - React frontend application
- public/ - Static frontend assets
- server/ - FastAPI backend and API routes
- server/routes/ - API endpoints for crowd and translation features
- server/config.py - Backend environment configuration
- server/gemini_service.py - Gemini AI service integration
- server/verify_backend.py - Backend QA verification script

## Prerequisites

Make sure you have the following installed:
- Node.js 18+ and npm
- Python 3.10+ or 3.11+
- Git

## 1. Clone the project

```bash
git clone <your-repository-url>
cd challenge-4
```

## 2. Install frontend dependencies

```bash
npm install
```

## 3. Set up the backend environment

Open a terminal in the project root and run:

```bash
cd server
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

Then install Python dependencies:

```bash
pip install -r requirements.txt
```

## 4. Configure environment variables

Create a `.env` file inside the server folder if you want to use real Gemini AI responses.

Example:

```env
GEMINI_API_KEY=your_google_gemini_api_key
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
DEBUG=false
```

If the API key is not set, the backend will run in mock mode and use built-in sample responses.

## 5. Run the backend

From the server folder:

```bash
python main.py
```

The backend will start on:
- http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs

## 6. Run the frontend

Open a second terminal in the project root and run:

```bash
npm run dev
```

Then open:
- http://localhost:5173/

## 7. Build for production

### Frontend build

```bash
npm run build
```

### Backend check

```bash
cd server
python verify_backend.py
```

## 8. Useful commands

### Run tests (backend)

From the project root run:

```bash
cd server
pip install -r requirements.txt
pytest -q
```

Continuous Integration:

This repository includes a GitHub Actions workflow at `.github/workflows/ci.yml` that runs backend tests and performs the frontend build on pushes and pull requests to `main`. Add `VITE_API_URL` to repository secrets in Settings for production builds.


### Frontend
```bash
npm run dev
npm run build
npm run lint
```

### Backend
```bash
cd server
python main.py
python verify_backend.py
```

## Notes

- The frontend expects the backend to be running on port 8000.
- If you deploy the frontend separately, set the Vite environment variable `VITE_API_URL` to your backend URL.
- The app is designed to work locally first and can be deployed with a production server setup afterward.

## Deploy to production

### Option 1: Backend on Render, frontend on Vercel

1. Backend deployment on Render
   - Create a new Web Service from the server folder.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - Environment variables:
     - `GEMINI_API_KEY=your_key`
     - `HOST=0.0.0.0`
     - `PORT=8000`
     - `FRONTEND_URL=https://your-frontend-domain.vercel.app`

2. Frontend deployment on Vercel
   - Import the repository into Vercel.
   - Build Command: `npm run build`
   - Output Directory: `dist`
   - Environment variable:
     - `VITE_API_URL=https://your-backend-domain.onrender.com`

3. Test the live app
   - Open the frontend URL.
   - Confirm the dashboard loads and translation requests reach the backend.

### Option 2: One-click deploy with Render static site

If you prefer a single-service deployment, you can also host the frontend as a static site and point it to the backend URL above.

## License

This project is for educational purposes.
