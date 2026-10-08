# TRACE

> A local-first exploration system that turns real-world physical discoveries into a living personal map, using those discoveries to influence what you should discover next.

---

## Concept

**Go outside. Notice more. Leave a trace.**

Modern technology usually competes for attention, pulling focus onto screens and virtual feeds. TRACE operates on an inverse principle:

> **The world is the interface. The screen should start and end the experience, not become the experience.**

When you explore outside and notice something—an unusual architectural flourish, a wild plant along a fence line, an old milestone, or a quiet alleyway—TRACE lets you capture that observation as a *trace*. Over time, your personal traces construct a living map of your surroundings, and local AI evaluates patterns to inspire your next exploration.

TRACE is designed from first principles as an exploration catalyst, not a social feed, not a fitness tracker, not a turn-by-turn navigation tool, and not a chatbot.

---

## Current Status

**Current State: Phase 0 — Foundation**

- Clean, decoupled architectural scaffold (Frontend + Backend).
- Minimal FastAPI backend with structured health endpoint and CORS configuration.
- Minimal React + TypeScript + Vite frontend shell verifying API connectivity.
- Architecture and repository hygiene specifications established.
- **Not yet implemented**: The map visualizer, trace capture pipeline, local AI interpretation, and exploration clue engine are planned for subsequent phases.

---

## Planned Architecture

TRACE uses a strictly decoupled, local-first stack:

```
[ Explorer ]
     │
     ▼
[ Frontend (React + TypeScript + Vite) ]
     │  (Local REST API)
     ▼
[ Backend (FastAPI + Pydantic) ]
     │  (Future Local HTTP Inference)
     ▼
[ Local AI (LM Studio + Gemma 3 4B) — Planned ]
```

---

## Technology Stack

### Frontend
- **Framework**: React 18
- **Language**: TypeScript
- **Bundler & Dev Server**: Vite
- **Styling**: Vanilla CSS with customized design tokens (no bulky component libraries)

### Backend
- **Framework**: FastAPI
- **Validation**: Pydantic v2 & Pydantic Settings
- **Server**: Uvicorn
- **Testing**: Pytest & HTTPX

### Planned AI Layer
- **Runtime**: LM Studio (local OpenAI-compatible server at `http://127.0.0.1:1234/v1`)
- **Primary Model**: Gemma 3 4B (open-weight, efficient local inference)
- **Zero Cloud AI Dependency**: No remote API keys or third-party cloud data leaks

---

## Privacy & Local-First Philosophy

- **Local Storage**: Traces, coordinates, and journal notes stay on your local device.
- **Local Intelligence**: AI model execution will run locally via LM Studio without transmitting data to external servers.
- **Zero Telemetry**: No third-party trackers, no advertising beacons, and no behavioral profiling.

---

## Local Development Quickstart

### Prerequisites
- Node.js (v20+ recommended)
- Python (v3.11+ recommended)

### 1. Backend Setup

```bash
# Move to backend directory
cd backend

# Create and activate a Python virtual environment
python -m venv .venv

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Verify backend health at: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

### 2. Frontend Setup

```bash
# In a separate terminal, move to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Open the dashboard in your browser at: [http://localhost:5173](http://localhost:5173)

---

## Future Roadmap

1. **Phase 0: Foundation** *(Current)* — Architecture, development environment, health checks, and visual shell.
2. **Phase 1: Trace Data & Core Models** — Schema definitions, local database persistence, and trace capture input.
3. **Phase 2: Local AI Integration** — LM Studio gateway, prompt contracts, and Gemma 3 4B qualitative classification.
4. **Phase 3: Personal Trace Map** — Local cartographic rendering, spatial clustering, and territory exploration.
5. **Phase 4: Adaptive Exploration Loop** — Frontier generation, emergent pattern synthesis, and exploration cues.

---

## License

This project is open-source under the [MIT License](LICENSE).
