# Enterprise BI Agent — Frontend

React + Vite interface for the existing FastAPI/LangGraph backend.

## Run locally

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Open the local URL printed by Vite.

Set `VITE_API_BASE_URL` to your API origin if you run the backend locally (for example, `http://localhost:8000`). The deployed API is the default.

## Features

- Natural-language analytics chat
- Live animated assistant robot (CSS animation; no external image required)
- SQL preview and returned result table
- Role selector for analyst, admin, and viewer
- Human approval flow using the existing `POST /approve` endpoint
- API connection status and useful error states

The frontend calls the existing `POST /query` and `POST /approve` endpoints. It does not mock analytics responses.

## CORS

The FastAPI service must allow the frontend origin. For local development, add the Vite origin (usually `http://localhost:5173`) to FastAPI CORS middleware. For deployment, add your deployed frontend origin too.