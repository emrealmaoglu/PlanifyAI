# 🏫 PlanifyAI

> AI-powered generative spatial planning platform for Turkish university campuses.

![Version](https://img.shields.io/badge/version-10.2.0-blue)
![Status](https://img.shields.io/badge/status-Production%20Ready-green)
![License](https://img.shields.io/badge/license-MIT-yellow)

## 🎯 Project Status

| Metric | Value |
|--------|-------|
| **Version** | v10.2.0 |
| **Phase** | Production Ready |
| **Unit Tests** | ✅ 35 PASSED |
| **Sprint** | 8 (Docs Finalize) |

## ✨ Features

- 🗺️ **OpenStreetMap Integration** - Automatic campus context fetching
- 🧬 **H-SAGA Optimizer** - Hybrid Simulated Annealing + Genetic Algorithm
- 🌬️ **Wind Comfort Analysis** - Wake zone and blockage calculation
- ☀️ **Solar Gain Optimization** - Shadow interference modeling
- 🏗️ **Turkish Regulations** - Dynamic setbacks, fire codes, slope limits
- 📊 **XAI Visualization** - Slope heatmaps, wind arrows, violation styling
- 💾 **Save/Load** - Export/import scenarios as JSON
- 🚨 **Error Boundary** - React crash recovery with retry
- 👋 **Toast Notifications** - Success/error/warning messages

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Mapbox Account (free tier OK)

### Backend

```bash
# Create virtual environment
python3 -m venv venv && source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set PYTHONPATH
export PYTHONPATH=$(pwd)

# Start API server
cd backend/api && python run.py
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local  # Add Mapbox token
npm run dev
```

### Verify Installation

```bash
python3 tests/simulate_user_journey.py
# Expected: 10/10 PASSED
```

## 📁 Project Structure

```
PlanifyAI/
├── backend/
│   ├── api/                     # FastAPI endpoints
│   └── core/
│       ├── domain/geometry/     # OSM service
│       ├── optimization/        # H-SAGA engine
│       ├── physics/             # Wind calculations
│       ├── terrain/             # DEM/slope analysis
│       └── visualization/       # XAI generators
├── frontend/
│   └── src/
│       ├── features/cockpit/    # Sidebar UI
│       ├── components/          # Map, Results
│       └── store/               # Zustand state
├── tests/
│   ├── unit/                    # Unit tests (constraint, storage)
│   ├── api/                     # API endpoint tests
│   └── integration/             # Integration tests
├── docs/
│   ├── research/                # 61 research papers
│   ├── AGENT_MEMORY.md          # Engineering decisions
│   └── RESEARCH_IMPLEMENTATION_STATUS.md
├── data/                        # SQLite DB, OSM cache
├── archive/                     # Legacy files
└── SYSTEM_ARCHITECTURE_AND_ROADMAP.md
```

## 🔬 Technical Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, FastAPI, NumPy, Shapely, PyMOO |
| **Frontend** | React 18, TypeScript, Mapbox GL JS, Zustand |
| **Optimization** | H-SAGA (SA 30% → NSGA-III 70%) |
| **Geospatial** | OSMnx, PyProj, Open-Elevation API |

## 📈 Development Roadmap

- [x] ~~Phase 6-10: Core Engine & Cleanup~~
- [x] ~~Sprint 1: Frontend Refactor~~
- [x] ~~Sprint 2: Backend Production (SQLite, Logging)~~
- [x] ~~Sprint 3: Test Suite (35 tests)~~
- [ ] Sprint 4: Performance (Parallel SA, R-tree)
- [ ] Future: WebSocket Updates, Case-Based AI

## 📄 License

MIT License - See [LICENSE](LICENSE)

## 👤 Author

**Emre Almaoğlu**  
Computer Science Graduation Project  
Kastamonu University - 2025

---

📖 See [SYSTEM_ARCHITECTURE_AND_ROADMAP.md](SYSTEM_ARCHITECTURE_AND_ROADMAP.md) for full technical documentation.
