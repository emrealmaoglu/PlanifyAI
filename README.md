# 🏫 PlanifyAI

AI-powered multi-objective spatial planning platform for university campus optimization.

## 🎯 Project Status

**Current Phase:** Phase 2 Complete ✅ | Phase 3 In Progress
**Version:** v0.3.0
**License:** MIT

## ✨ Key Features

### 🧬 Multi-Objective Optimization
- **NSGA-III**: State-of-the-art many-objective evolutionary algorithm
- **AdaptiveHSAGA**: Hybrid Simulated Annealing + Genetic Algorithm with adaptive operators
- **4 Objective Profiles**: Standard, Research-Enhanced, 15-Minute City, Campus Planning

### 🎯 Research-Based Objectives
- **Cost Optimization**: Construction and land use costs
- **Walking Distance**: Tobler's Hiking Function with slope-adjusted accessibility
- **Adjacency**: Gravity models for building relationships
- **Diversity**: Shannon Entropy for service distribution
- **Accessibility**: Two-Step Floating Catchment Area (2SFCA) analysis

### 📊 Professional Visualization
- 2D/3D Pareto front plots
- Parallel coordinates for multi-dimensional analysis
- Objective trade-off matrices
- Statistical analysis and comparison tools

### ⚡ Performance Benchmarking
- Comprehensive algorithm comparison framework
- Standardized test cases (small, medium, large)
- Performance metrics: runtime, memory, solution quality
- Statistical analysis with multiple runs

### 🚀 REST API
- FastAPI-based backend with OpenAPI documentation
- NSGA-III optimization endpoint
- Visualization generation endpoints
- Objective profile management

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/PlanifyAI.git
cd PlanifyAI

# Setup virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Optimization

```python
from backend.core.optimization.nsga3_runner import NSGA3Runner, NSGA3RunnerConfig
from src.algorithms import Building, BuildingType, ProfileType

# Define buildings
buildings = [
    Building(id="library", type=BuildingType.LIBRARY, area=3000, floors=3),
    Building(id="dorm", type=BuildingType.RESIDENTIAL, area=4000, floors=5),
    Building(id="cafeteria", type=BuildingType.DINING, area=1500, floors=2),
]

# Configure optimization
config = NSGA3RunnerConfig(
    population_size=50,
    n_generations=50,
    objective_profile=ProfileType.RESEARCH_ENHANCED,
    seed=42
)

# Run NSGA-III
runner = NSGA3Runner(buildings, bounds=(0, 0, 500, 500), config=config)
result = runner.run()

# Access results
print(f"Pareto front size: {result['pareto_size']}")
print(f"Best compromise: {result['best_compromise']}")
```

### Run Benchmarks

```bash
# Quick benchmark example
python examples/benchmark_example.py

# Comprehensive benchmarking
python benchmarks/run_benchmarks.py --category all --runs 10

# Specific test case
python benchmarks/run_benchmarks.py --test-case medium_university --runs 5
```

### Start API Server

```bash
cd backend
uvicorn api.main:app --reload

# Visit http://localhost:8000/docs for interactive API documentation
```

## 📊 Objective Profiles

### 1. **Standard** (Default)
- Basic 3-objective optimization
- Equal weights (0.33 each)
- Best for: Quick testing and simple scenarios

### 2. **Research-Enhanced** (Recommended)
- Enhanced 4-objective optimization with research-based functions
- Objectives: Cost, Walking (2SFCA), Adjacency, Diversity (Shannon Entropy)
- Balanced weights (0.25 each)
- Best for: High-quality campus planning with scientific rigor

### 3. **15-Minute City**
- Accessibility-focused planning
- Heavy emphasis on walking accessibility (0.5 weight)
- Elderly walking speed (3.6 km/h)
- Best for: Urban planning with walkability priority

### 4. **Campus Planning**
- Adjacency-focused for educational facilities
- Emphasizes building relationships (0.5 weight)
- Best for: Campus layout optimization

### Custom Profiles

```python
from src.algorithms import ObjectiveProfile

custom = ObjectiveProfile(
    name="Custom Profile",
    description="My custom optimization profile",
    use_enhanced=True,
    weights={
        "cost": 0.3,
        "walking": 0.3,
        "adjacency": 0.2,
        "diversity": 0.2
    },
    walking_speed_kmh=4.5
)
```

## 🏗️ Architecture

```
PlanifyAI/
├── backend/
│   ├── api/                    # REST API (FastAPI)
│   │   ├── routers/           # API endpoints
│   │   │   ├── nsga3.py       # NSGA-III optimization
│   │   │   └── visualization.py # Visualization generation
│   │   └── schemas/           # Pydantic models
│   ├── core/
│   │   └── optimization/      # Algorithm runners
│   │       ├── nsga3_runner.py
│   │       └── adaptive_hsaga_runner.py
│   └── tests/                 # Unit & integration tests
├── src/
│   ├── algorithms/            # Core algorithms
│   │   ├── nsga3/            # NSGA-III implementation
│   │   ├── hsaga_adaptive.py # AdaptiveHSAGA
│   │   ├── fitness.py        # Fitness evaluation
│   │   ├── objectives.py     # Basic objectives
│   │   └── objectives_enhanced.py # Research-based objectives
│   └── visualization/         # Visualization tools
│       └── pareto_visualization.py
├── benchmarks/                # Benchmarking framework
│   ├── benchmark_runner.py   # Benchmark execution
│   ├── benchmark_reporter.py # Report generation
│   └── test_cases.py         # Standardized test cases
└── examples/                  # Usage examples
    ├── nsga3_complete_workflow.py
    ├── api_usage_examples.py
    └── benchmark_example.py
```

## 📈 Performance Metrics

Based on comprehensive benchmarking (as of 2026-01-03):

### NSGA-III
- **Runtime**: ~2.5s (small), ~15s (medium), ~45s (large)
- **Pareto Front Size**: 25-35 solutions
- **Hypervolume**: High quality Pareto fronts
- **Best For**: Many-objective problems (3+ objectives)

### AdaptiveHSAGA
- **Runtime**: ~3.2s (small), ~18s (medium), ~60s (large)
- **Pareto Front Size**: 12-20 solutions
- **Hypervolume**: Competitive quality
- **Best For**: Problems requiring adaptive exploration

*Note: Actual performance varies based on problem complexity and configuration.*

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov=backend --cov-report=html

# Run specific test suite
pytest backend/tests/unit/test_nsga3_runner.py
pytest backend/tests/integration/test_nsga3_api.py

# Run benchmarks
python benchmarks/run_benchmarks.py --category small
```

**Test Statistics:**
- 215+ unit and integration tests
- All tests passing ✅
- Coverage: 70%+ for core modules

## 📚 Documentation

- **[Examples README](examples/README.md)** - Complete usage examples
- **[Benchmarks README](benchmarks/README.md)** - Benchmarking guide
- **[Development Roadmap](DEVELOPMENT_ROADMAP.md)** - Project progress
- **[API Documentation](http://localhost:8000/docs)** - Interactive API docs (when server running)

## 🎓 Research Foundation

This project implements state-of-the-art research in spatial optimization:

1. **NSGA-III** (Deb & Jain, 2014) - Reference point-based many-objective optimization
2. **Two-Step Floating Catchment Area** (Luo & Wang, 2003) - Accessibility analysis
3. **Shannon Entropy** (Shannon, 1948) - Service diversity measurement
4. **Tobler's Hiking Function** (Tobler, 1993) - Realistic walking distance with terrain
5. **Gravity Models** - Spatial interaction and building relationships
6. **Adaptive Cooling Schedules** - Variance-based temperature control for SA

## 🔧 API Endpoints

### NSGA-III Optimization
```bash
POST /api/nsga3/optimize
GET  /api/nsga3/profiles
GET  /api/nsga3/health
```

### Visualization
```bash
POST /api/visualize/pareto-2d
POST /api/visualize/pareto-3d
POST /api/visualize/parallel-coordinates
POST /api/visualize/objective-matrix
POST /api/visualize/statistics
GET  /api/visualize/health
```

## 📊 Project Statistics

- **Total Code**: ~20,000 lines
- **Algorithms**: 2 (NSGA-III, AdaptiveHSAGA)
- **Objective Profiles**: 4 predefined + custom support
- **API Endpoints**: 38 across 8 routers
- **Test Cases**: 215+ (unit + integration)
- **Benchmark Test Cases**: 6 standardized scenarios
- **Documentation**: Comprehensive READMEs and examples

## 🗺️ Roadmap

- [x] **Phase 1**: Core Algorithms (NSGA-III, AdaptiveHSAGA) ✅
- [x] **Phase 2**: Integration & Usability ✅
  - [x] ObjectiveProfile system
  - [x] REST API endpoints
  - [x] Visualization system
  - [x] Performance benchmarking
- [ ] **Phase 3**: Advanced Features (In Progress)
  - [x] AdaptiveHSAGA ObjectiveProfile support ✅
  - [ ] Algorithm parameter tuning
  - [ ] Enhanced documentation
- [ ] **Phase 4**: Frontend Application
- [ ] **Phase 5**: Production Deployment

See [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) for detailed progress.

## 🤝 Contributing

This is a graduation project, but suggestions and feedback are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 👤 Author

**Emre Almaoğlu**
Computer Science Graduation Project
Kastamonu University - 2025

## 🙏 Acknowledgments

- Prof. [Advisor Name] for guidance and support
- Research papers that formed the theoretical foundation
- Open-source community for excellent tools and libraries

---

**Built with**: Python, FastAPI, NumPy, Matplotlib, Pytest
**Algorithms**: NSGA-III, AdaptiveHSAGA, Simulated Annealing, Genetic Algorithms
**Research Areas**: Multi-objective optimization, Spatial planning, Evolutionary computation
