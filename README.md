# 🏛️ PlanifyAI

**AI-Powered Generative Campus Planning Platform**

> Automated spatial planning using hybrid optimization algorithms and semantic tensor fields

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📋 Project Status

**🚀 Week 1 (Nov 3-10, 2025):** Setup & Core Algorithm
**Progress:** 🟩🟩🟩🟩⬜⬜⬜⬜ 40%

### Current Week Goals
- [x] Development environment setup (Day 1)
- [x] H-SAGA SA phase implementation (Day 2)
- [x] Research-based objective functions (Day 3) ✅
- [x] H-SAGA GA phase implementation (Day 4) ✅
- [x] Unit tests (88% coverage for hsaga.py, 75% overall) (Day 4)
- [ ] Integration & optimization (Days 6-7)

### Day 4 Progress (Nov 7, 2025)

**✅ H-SAGA Complete Implementation**

**Genetic Algorithm Implementation:**
- ✅ Population initialization (SA-seeded: 50/30/20 strategy)
- ✅ Tournament selection (bias toward fitness)
- ✅ Uniform crossover (0.8 rate)
- ✅ Multi-operator mutation (Gaussian 70%, Swap 20%, Reset 10%)
- ✅ Elitist replacement strategy

**Full H-SAGA Pipeline:**
- ✅ Stage 1: Simulated Annealing (global exploration, 4 parallel chains)
- ✅ Stage 2: Genetic Algorithm (local refinement, 50 pop × 50 gen)
- ✅ Complete optimize() method with comprehensive statistics
- ✅ Convergence tracking and result analysis

**Performance:**
- ✅ 10 buildings: <30 seconds (target met - actual: ~1s)
- ✅ Quality: GA improves SA results by 5-15%
- ✅ All integration tests passing

**Code Quality:**
- Test Coverage: 88% for hsaga.py, 75% overall
- Unit Tests: 17 tests (GA operators)
- Integration Tests: 5 tests (full pipeline)
- Benchmark: Performance validated

---

## 🎯 Project Overview

PlanifyAI automates campus spatial planning using:

- **H-SAGA Algorithm:** Hybrid Simulated Annealing + Genetic Algorithm
- **Semantic Tensor Fields:** Building-type aware road network generation
- **Multi-Objective Optimization:** Cost, accessibility, adjacency, sustainability
- **Interactive UI:** Bilingual (Turkish/English) web interface

**Target Domain:** Turkish university campus planning (POC)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+ (required)
- Apple M1/M2/M3 Mac (optimized) or Intel Mac
- 8GB+ RAM recommended

### Installation

```bash
# Clone repository
git clone https://github.com/emrealmaoglu/planifyai.git
cd planifyai

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python verify_setup.py
```

**Expected output:**
```
✅ VERIFICATION PASSED!
   You're ready to start coding! 🎉
```

---

## 🏗️ Project Structure

```
planifyai/
├── src/                    # Source code
│   ├── algorithms/         # Optimization algorithms
│   ├── spatial/            # Spatial planning modules
│   ├── data/               # Data processing
│   ├── ui/                 # User interface
│   └── utils/              # Utility functions
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── benchmarks/         # Performance benchmarks
├── docs/                   # Documentation
├── data/                   # Data files
├── notebooks/              # Jupyter notebooks
└── config/                 # Configuration files
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_hsaga.py -v

# Run benchmarks
pytest tests/benchmarks/ --benchmark-only

# Run performance benchmarks
python scripts/run_benchmarks.py
```

---

## 🔬 Performance Profiling

PlanifyAI includes built-in performance profiling utilities:

```python
from src.utils.profiling import profile_optimization

@profile_optimization
def optimize():
    # Your optimization code
    pass
```

Profiles are automatically saved to `outputs/` directory. Use `snakeviz` to visualize:

```bash
pip install snakeviz
snakeviz outputs/optimize_profile.prof
```

**Example usage:**
```python
from src.utils.profiling import profile_function, analyze_profile
import cProfile

# Profile a function
profiler = cProfile.Profile()
profiler.enable()

result = optimizer.optimize()

profiler.disable()
analyze_profile(profiler, top_n=20)
```

---

## 📊 Development Progress

### Week 1: Setup & Core Algorithm
- [x] Day 1: Environment setup ✅
- [x] Day 2: Simulated Annealing ✅
- [x] Day 3: Research-based objective functions ✅
  - Construction cost minimization
  - Walking distance (15-minute city)
  - Adjacency satisfaction
- [ ] Day 4: Genetic Algorithm
- [ ] Day 5: Extended unit testing
- [ ] Day 6-7: Integration & polish

### Week 2-3: Spatial Features
- [ ] Tensor field generation
- [ ] Road network generation (RK4 integration)
- [ ] NSGA-III multi-objective optimization
- [ ] Constraint handling

### Week 4: User Interface
- [ ] Streamlit web app
- [ ] Interactive map visualization
- [ ] TR/EN language toggle
- [ ] Results export

### Week 5-8: Documentation & Finalization
- [ ] Code documentation
- [ ] Thesis writing
- [ ] Defense preparation
- [ ] Final testing & deployment

---

## 🛠️ Tech Stack

**Core:**
- Python 3.11
- NumPy (OpenBLAS/Accelerate) - 2-5x speedup on M1
- SciPy, pandas, GeoPandas

**Optimization:**
- pymoo (NSGA-III)
- DEAP (GA primitives)
- Custom H-SAGA implementation

**Visualization:**
- Streamlit (web UI)
- Plotly, matplotlib
- Folium (maps)

**Development:**
- pytest, black, pylint, mypy
- Git, GitHub

---

## 📈 Performance

**Target (MVP):**
- 50-100 buildings: < 2 minutes
- Test coverage: ≥ 80%
- Code quality: Pylint score ≥ 8.0

**M1 Optimization:**
- NumPy with OpenBLAS (2-3x speedup, pip-installed) or Apple Accelerate (3-5x speedup, conda)
- Multiprocessing for SA chains (4 cores)
- Vectorized operations

**Note:** Pip-installed NumPy uses OpenBLAS which is optimized for ARM64/M1. For maximum performance with Apple Accelerate, use conda:
```bash
conda install numpy 'libblas=*=*accelerate'
```

---

## 📚 Documentation

- [Architecture Overview](docs/architecture.md) (Coming soon)
- [API Documentation](docs/api/) (Coming soon)
- [User Guide](docs/user-guide.md) (Coming soon)
- [Developer Guide](docs/developer-guide.md) (Coming soon)

---

## 🤝 Contributing

This is an academic project (CS graduation thesis). Contributions welcome after v1.0 release (Dec 2025).

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 👤 Author

**[Your Name]**
Computer Science / Engineering Student
[University Name]

- GitHub: [@emrealmaoglu](https://github.com/emrealmaoglu)
- Email: your.email@example.com

---

## 🙏 Acknowledgments

- Research based on 52+ academic papers and industry reports
- Inspired by Parish & Müller's tensor field method
- Built with ❤️ using Python and AI tools (Claude, Cursor)

---

## 📅 Timeline

**Start:** November 3, 2025
**MVP Deadline:** December 30, 2025 (8 weeks)
**Defense:** January 2026

---

**Status:** 🟢 Active Development

## Day 3 Progress (Nov 6, 2025)

### ✅ Research-Based Objectives Implemented

**New Modules:**
- `src/algorithms/objectives.py` - Pure objective functions
  - `minimize_cost()` - Construction cost minimization (TL/m²)
  - `minimize_walking_distance()` - 15-minute city accessibility
  - `maximize_adjacency_satisfaction()` - Building type compatibility

**Updated Modules:**
- `src/algorithms/fitness.py` - Refactored to use research-based objectives
  - Backwards compatible with Day 1-2 code
  - All SA tests pass without changes

**Performance:**
- Cost objective: <0.1ms for 100 buildings
- Walking distance: <0.1ms for 100 buildings
- Adjacency: <5.2ms for 100 buildings

**Test Coverage:** 98% (objectives module), 87% overall

Last updated: 2025-11-06
