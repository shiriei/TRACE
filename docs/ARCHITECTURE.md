# TRACE — System Architecture Specification

## 1. Project Purpose

**TRACE** is a local-first exploration system engineered to get people away from digital screens and back into the physical world.

> **Core Concept:** TRACE turns the things a person discovers outside into a living personal map, and uses those discoveries to influence what they should discover next.

### Design Principles
1. **The world is the interface**: The screen should start and end the experience, not become the experience.
2. **Local-first sovereignty**: Observations, spatial trails, and personal notes remain entirely on the user's local hardware.
3. **Curiosity-driven progression**: Real-world observations expand a personal cartographic frontier rather than completing rigid, gamified task checklists.
4. **Authentic scope**: TRACE is *not* a chatbot, *not* a generic navigation app, *not* a social media feed, and *not* a scavenger hunt clone.

---

## 2. High-Level Architecture

The system follows a cleanly decoupled three-tier architecture:

```
┌─────────────────────────────────┐
│       Frontend (Client)         │
│   React + TypeScript + Vite     │
└────────────────┬────────────────┘
                 │ HTTP / REST (local)
                 ▼
┌─────────────────────────────────┐
│       Backend (Server)          │
│       FastAPI + Pydantic        │
└────────────────┬────────────────┘
                 │ Local OpenAI-compatible API
                 ▼
┌─────────────────────────────────┐
│     Future Local AI Layer       │
│  LM Studio + Gemma 3 4B (Local) │
│       [Planned — Phase 2]       │
└─────────────────────────────────┘
```

- **Frontend Tier**: Lightweight browser interface for field note entry, status checks, and spatial visualization.
- **Backend Tier**: Local service orchestrating data validation, domain logic, persistence, and inference routing.
- **Local AI Tier (Planned)**: Local open-weight inference engine running via LM Studio without external cloud API dependencies.

---

## 3. Component & Directory Responsibilities

### Frontend (`frontend/src/`)
- **`components/`**: Reusable UI elements (cards, headers, buttons, status indicators).
- **`features/`**: Feature-specific modules (future trace map, exploration loggers, insight drawers).
- **`hooks/`**: Custom React hooks for backend polling, responsive layout, and device events.
- **`pages/`**: Top-level screen views (Dashboard/Landing shell, future map explorer).
- **`services/`**: Centralized API clients; encapsulation of network requests and base URLs.
- **`types/`**: TypeScript interfaces and domain type contracts matching backend schemas.
- **`utils/`**: Formatting, date helpers, coordinate transformations.
- **`assets/`**: Static assets, branding marks, and SVG icons.

### Backend (`backend/app/`)
- **`core/`**: Central configuration (`config.py`), environment variable management, CORS policies, and logging setups.
- **`api/`**: API route definitions and endpoint controllers. Handlers should remain thin, delegating logic to services.
- **`schemas/`**: Pydantic models for request bodies, query parameters, and serializable response contracts.
- **`models/`**: Domain models and future data persistence entities (e.g. SQLite tables).
- **`services/`**: Core business logic, spatial computations, and future local AI client wrappers.
- **`main.py`**: Application bootstrap, middleware registration, router mounting, and global exception handlers.

---

## 4. Planned TRACE Core Flow

The long-term lifecycle of an explorer's journey through TRACE follows this conceptual pipeline:

```mermaid
flowchart TD
    A[User] -->|Steps outside| B[Exploration]
    B -->|Notices something notable| C[Observation]
    C -->|Logs note & coordinates| D[Trace Capture]
    D -.->|Evaluates qualitative note [Planned]| E[Local AI Interpretation]
    E -.->|Updates territory & connections [Planned]| F[Personal Trace Map]
    F -.->|Identifies emergent themes [Planned]| G[Pattern / Connection Discovery]
    G -.->|Generates evocative clues [Planned]| H[Next Exploration]
    H -->|Prompts user outside| A
```

| Flow Stage | Description | Status |
| :--- | :--- | :--- |
| **User** | Explorer setting their focus onto the physical world | Active |
| **Exploration** | Walking, wandering, and observing immediate surroundings | Active |
| **Observation** | Sensory notices (landmarks, flora, masonry, signs, sounds) | Planned |
| **Trace Capture** | Logging raw observation, timestamp, and optional coordinates | Planned |
| **Local AI Interpretation** | Gemma 3 4B categorizes sensory themes and extracts qualitative meaning | Planned |
| **Personal Trace Map** | Traces render on a personalized, evolving local map | Planned |
| **Pattern / Connection Discovery** | System discovers relationships between isolated traces | Planned |
| **Next Exploration** | Generates adaptive, enigmatic clues for where to explore next | Planned |

---

## 5. Privacy & Local-First Philosophy

- **Zero Cloud Tracking**: All personal traces, timestamps, and coordinates are stored strictly on the user's device.
- **Local AI Inference**: When AI capabilities are enabled in future phases, inference will communicate with a local LM Studio instance (`http://127.0.0.1:1234`). Personal traces will never be transmitted to third-party cloud APIs.
- **No Third-Party Analytics**: No Google Analytics, telemetry pings, advertising SDKs, or external trackers.

---

## 6. Repository Hygiene & Git Cleanliness

To preserve repository integrity and protect developer confidentiality, the following items **must never be committed to Git**:

1. **Secrets & Configurations**: `.env`, `.env.local`, API keys, certificates. (Only `.env.example` is committed).
2. **AI Weights & Model Files**: `*.gguf`, `*.bin`, `*.safetensors`, `*.pt`, `*.onnx`, `models/`, `.lmstudio/`.
3. **Dependencies**: `node_modules/`, `.venv/`, `venv/`.
4. **Build Output & Caches**: `dist/`, `build/`, `.vite/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`.
5. **Runtime Databases & Logs**: `*.sqlite`, `*.db`, `*.log`, `logs/`, `runtime/`.
6. **Machine-Specific & OS Metadata**: `.DS_Store`, `Thumbs.db`, `desktop.ini`, IDE directories.
