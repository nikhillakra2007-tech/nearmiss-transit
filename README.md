<div align="center">

# 🚊 NearMiss Transit — Operational Pre-Disruption Intelligence

### *See the recurring signals between normal service and system failure — before the next disruption occurs.*

<br/>

[![Live Production](https://img.shields.io/badge/🚀_LIVE_PRODUCTION-wcc--tawny.vercel.app-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://wcc-tawny.vercel.app)
[![Surveillance Workspace](https://img.shields.io/badge/🛰️_SURVEILLANCE_WORKSPACE-Open_Dashboard-10b981?style=for-the-badge&logo=google-cloud&logoColor=white)](https://wcc-tawny.vercel.app/workspace)
[![API Documentation](https://img.shields.io/badge/📑_API_DOCS-Swagger_OpenAPI-0284c7?style=for-the-badge&logo=fastapi&logoColor=white)](https://wcc-tawny.vercel.app/docs)

<br/>

[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Frontend](https://img.shields.io/badge/Frontend-Modular_ES6+-f7df1e?style=for-the-badge&logo=javascript&logoColor=black)](./frontend/components)
[![Styling](https://img.shields.io/badge/Styling-Custom_CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](./frontend/css)
[![Database](https://img.shields.io/badge/Database-SQLAlchemy_2.0-D71F00?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlalchemy.org/)
[![Telemetry](https://img.shields.io/badge/Telemetry-GTFS--Realtime-F58220?style=for-the-badge&logo=google-maps&logoColor=white)](https://gtfs.org/realtime/)
[![Deployment](https://img.shields.io/badge/Deployment-Vercel_Edge-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://wcc-tawny.vercel.app)
[![Architecture](https://img.shields.io/badge/Architecture-Decoupled_1--2_Files-8B5CF6?style=for-the-badge&logo=blueprint&logoColor=white)](./frontend/components)

<br/>

[🌐 **Live Landing Page**](https://wcc-tawny.vercel.app) • [🛰️ **Surveillance Workspace**](https://wcc-tawny.vercel.app/workspace) • [📖 **Interactive API Docs**](https://wcc-tawny.vercel.app/docs) • [📁 **Frontend Components**](./frontend/components)

</div>

---

## 🔗 Live Deployments & Endpoints

| Environment | Service | Live URL | Status |
|---|---|---|---|
| **Production** | 🌐 Public Landing Page | [https://wcc-tawny.vercel.app](https://wcc-tawny.vercel.app) | ![Active](https://img.shields.io/badge/ONLINE-brightgreen?style=flat-square) |
| **Operations** | 🛰️ Surveillance Workspace | [https://wcc-tawny.vercel.app/workspace](https://wcc-tawny.vercel.app/workspace) | ![Active](https://img.shields.io/badge/ONLINE-brightgreen?style=flat-square) |
| **API Reference** | 📑 Interactive Swagger UI | [https://wcc-tawny.vercel.app/docs](https://wcc-tawny.vercel.app/docs) | ![Active](https://img.shields.io/badge/ONLINE-brightgreen?style=flat-square) |
| **API Health** | 🩺 Telemetry & DB Health | [https://wcc-tawny.vercel.app/api/v1/health](https://wcc-tawny.vercel.app/api/v1/health) | ![Active](https://img.shields.io/badge/200_OK-brightgreen?style=flat-square) |
| **Ingestion Engine**| ⚡ Live / Replay Cycle Trigger | `POST /api/v1/ingestion/run` | ![Active](https://img.shields.io/badge/READY-brightgreen?style=flat-square) |

---

## 📸 Visual Showcase

### Surveillance Workspace & Real-Time Operational Intelligence
![Workspace Dashboard](./docs/images/workspace-dashboard.png)

### Deep-Dive Investigation, Delay Timelines & Replay
![Investigation Detail](./docs/images/investigation-detail.png)

### Interactive Landing Experience & Illustrative Transit Network
![Landing Hero](./docs/images/landing-hero.png)

### Route Resilience Radar & Stress Scoring
![Resilience Radar](./docs/images/resilience-radar.png)

---

## ⚡ The Core Problem

Transit control centers are flooded with delay alerts only **after** lines break down. 

**NearMiss Transit shifts surveillance upstream:**
- Most service deviations escalate, recover, and repeat quietly under standard thresholds.
- When two separate routes experience correlated micro-delays, they form a **domino chain** that cascades into gridlock.
- NearMiss Transit detects, correlates, forecasts, and simulates these near-misses in real time with 100% evidence-backed traceability.

```
DETECT ──> REMEMBER ──> CONNECT ──> FORECAST ──> REPLAY ──> SIMULATE ──> RECOMMEND ──> VERIFY
```

---

## 🛠️ Tech Stack & Engineering Matrix

| Layer | Badges & Technology | Purpose & Implementation |
|---|---|---|
| **Backend Core** | [![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com) [![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org) [![Uvicorn](https://img.shields.io/badge/Uvicorn-2C3E50?style=flat-square&logo=gunicorn&logoColor=white)](https://www.uvicorn.org/) | High-performance asynchronous REST API, route handlers, dependency injection |
| **Data & ORM** | [![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-D71F00?style=flat-square&logo=python&logoColor=white)](https://www.sqlalchemy.org/) [![Alembic](https://img.shields.io/badge/Alembic-000000?style=flat-square)](https://alembic.sqlalchemy.org/) [![SQLite](https://img.shields.io/badge/SQLite_3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org) | Declarative relational schema, pool pre-ping, auto-migrations, serverless `/tmp` fallback |
| **Telemetry Ingestion** | [![GTFS](https://img.shields.io/badge/GTFS--Realtime-F58220?style=flat-square&logo=transit&logoColor=white)](https://gtfs.org/realtime/) [![Protobuf](https://img.shields.io/badge/Protocol_Buffers-4285F4?style=flat-square&logo=google&logoColor=white)](https://protobuf.dev/) | Live VehiclePositions & TripUpdates parsing, noise filtering, timestamp normalization |
| **Intelligence Services** | [![Engine](https://img.shields.io/badge/Pattern_Detector-8B5CF6?style=flat-square)](./backend/app/services/patterns) [![Chains](https://img.shields.io/badge/Chain_Detector-6366F1?style=flat-square)](./backend/app/services/chains) [![Forecast](https://img.shields.io/badge/Forecast_Engine-EC4899?style=flat-square)](./backend/app/services/forecast) | Deviation-escalation-recovery sequence detection, multi-hop temporal dominoes, risk scoring |
| **Frontend Architecture** | [![Modular JS](https://img.shields.io/badge/Vanilla_ES6+_Modules-F7DF1E?style=flat-square&logo=javascript&logoColor=black)](./frontend/components) [![Architecture](https://img.shields.io/badge/1--2_Files_Per_Folder-10B981?style=flat-square)](./frontend/components) | Decoupled component architecture: zero giant monolithic script files, instant fault isolation |
| **Styling & Motion** | [![CSS3](https://img.shields.io/badge/Pure_CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)](./frontend/css) [![Lenis](https://img.shields.io/badge/Lenis_Scroll-000000?style=flat-square)](./frontend/assets) [![SVG](https://img.shields.io/badge/Custom_SVG_Charts-FF9800?style=flat-square)](./frontend/components/charts) | Bespoke typography, parallax network canvas, inline progression curves, zero UI frameworks |
| **Deployment & Edge** | [![Vercel](https://img.shields.io/badge/Vercel_Serverless-000000?style=flat-square&logo=vercel&logoColor=white)](https://vercel.com) [![Edge CDN](https://img.shields.io/badge/Edge_CDN-000000?style=flat-square&logo=fastly&logoColor=white)](https://vercel.com) | Serverless Python backend function (`api/index.py`) + edge-cached static distribution |

---

## 🏛️ Clean Architecture Breakdown

The project separates concerns strictly into deterministic core services and decoupled UI modules:

```
wcc/
├── backend/app/                 # FastAPI Core Services
│   ├── api/routes/              # REST Endpoints (health, nearmisses, patterns, forecast, etc.)
│   ├── core/                    # Config, security, and logging
│   ├── db/                      # SQLAlchemy session and models
│   ├── models/                  # Database entity schemas
│   └── services/                # Specialized intelligence engines
│       ├── ingestion/           # GTFS-RT normalization and ingestion
│       ├── detection/           # Near-miss detector (deviation + escalation + recovery)
│       ├── patterns/            # Pattern clustering and fingerprinting
│       ├── chains/              # Multi-hop domino association detector
│       ├── forecast/            # Early-warning risk score evaluator
│       └── counterfactual/      # What-if scenario intervention simulator
│
├── frontend/                    # Zero-Bloat Modular Frontend
│   ├── index.html               # High-impact illustrative landing page
│   ├── workspace.html           # Surveillance operations dashboard
│   ├── css/                     # Scoped stylesheets (landing, workspace, base)
│   └── components/              # Decoupled component architecture (1-2 files per folder)
│       ├── core/                # api-client.js, state-store.js
│       ├── charts/              # sparkline.js, timeline-chart.js
│       ├── status-bar/          # status-bar.js (telemetry health & ingestion trigger)
│       ├── nearmiss-feed/       # nearmiss-feed.js (active near-miss cards)
│       ├── resilience-radar/    # resilience-radar.js (stress scores by corridor)
│       ├── forecast-monitor/    # forecast-monitor.js (early-warning signals)
│       ├── pattern-catalog/     # pattern-catalog.js (recurring incident memory)
│       ├── investigation-panel/ # investigation-panel.js (timelines, replay & lab)
│       ├── operations-live/     # operations-live.js (GTFS vehicle/event telemetry)
│       ├── navigation/          # workspace-nav.js (smooth section tracking)
│       ├── landing-hero/        # hero-network.js (parallax SVG network scene)
│       └── landing-atlas/       # stage-atlas.js (interactive 3-stage atlas)
│
├── docs/                        # Architecture specs, verification docs & screenshots
├── scripts/                     # Seed utilities and simulation scripts
├── api/index.py                 # Vercel Serverless Function entrypoint
└── vercel.json                  # Vercel deployment routing configuration
```

---

## 🚀 Quickstart & Local Run

### 1. Clone & Set Up Virtual Environment

```bash
git clone https://github.com/nikhillakra2007-tech/nearmiss-transit.git
cd nearmiss-transit

python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Seed Demo Transit Telemetry (Optional)

```bash
python scripts/seed_demo.py
```

### 3. Start the Server

```bash
# Set demo mode for offline replay and simulation
# Windows PowerShell:
$env:DEMO_MODE="true"; python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765

# Linux / macOS:
DEMO_MODE=true python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

- **Landing Page:** [http://127.0.0.1:8765/](http://127.0.0.1:8765/)
- **Surveillance Workspace:** [http://127.0.0.1:8765/workspace](http://127.0.0.1:8765/workspace)
- **Interactive OpenAPI Docs:** [http://127.0.0.1:8765/docs](http://127.0.0.1:8765/docs)

---

## 🔬 Intelligence Modules

### 1. Near-Miss Signature Detector
Does not rely on a simple `delay > X` rule. Identifies genuine operational signatures consisting of:
- **Deviation Window** (initial departure from normal run-time)
- **Escalation Phase** (steepening delay gradient)
- **Recovery Event** (stabilization before terminal delay)

### 2. Domino Chains & Multi-Hop Propagation
Tracks cross-route dependencies (e.g., `Route 42 → Lightrail Green-E → Route 1`). Computes recurrence strength, average temporal gap, and confidence without conflating correlation with causation.

### 3. Counterfactual Simulation Lab
Simulate operational interventions directly against observed telemetry:
- *Reduce peak delay by X%*
- *Trigger recovery N minutes earlier*
- *Reduce recovery duration by X%*
View side-by-side SVG comparison graphs with modeled outcome metrics.

---

## 🌐 Deploy to Vercel

The project includes built-in Vercel configuration (`vercel.json` + `api/index.py`).

```bash
npm i -g vercel
vercel --prod
```

**Live Production Link:** [https://wcc-tawny.vercel.app](https://wcc-tawny.vercel.app)

---

## 📄 License
MIT License. Built for resilient, evidence-grounded municipal transit intelligence.
