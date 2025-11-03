# 🏛️ PlanifyAI

**AI-Powered Generative Campus Planning Platform**

> Automated spatial planning using hybrid optimization algorithms and semantic tensor fields

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

---

## 📋 Project Status

**🚀 Week 1 (Nov 3-10, 2025):** Setup & Core Algorithm  
**Progress:** 🟩🟩🟩⬜⬜⬜⬜⬜ 25%

### Current Week Goals
- [x] Development environment setup (Day 1)
- [ ] H-SAGA algorithm implementation (Days 2-3)
- [ ] Multi-objective fitness functions (Day 4)
- [ ] Unit tests (80%+ coverage) (Day 5)
- [ ] Integration & optimization (Days 6-7)

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
```

---

## 📊 Development Progress

### Week 1: Setup & Core Algorithm
- [x] Day 1: Environment setup ✅
- [ ] Day 2: Simulated Annealing
- [ ] Day 3: Genetic Algorithm
- [ ] Day 4: Fitness functions
- [ ] Day 5: Unit testing
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
- NumPy (Apple Accelerate) - 3x speedup on M1
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
- NumPy with Apple Accelerate (3-5x speedup)
- Multiprocessing for SA chains (4 cores)
- Vectorized operations

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

Last updated: 2025-11-03
