# 🎯 PlanifyAI - 8 Haftalık MVP Roadmap ve Teknik Analiz
## Üniversite Bitirme Projesi - Apple M1 MacBook Air

**Proje Başlangıç:** 4 Kasım 2025  
**Teslim Tarihi:** 30 Aralık 2025 (8 hafta)  
**Hedef:** MVP (Minimum Viable Product) - Çalışan demo + akademik teslim

---

## 📊 EXECUTIVE SUMMARY

### Proje Tanımı
**PlanifyAI:** AI-powered generative spatial planning platform  
**POC Domain:** University campus planning (Turkish universities)  
**Core Innovation:** Hybrid optimization (H-SAGA) + Semantic tensor fields for road generation  
**Deliverable:** Web-based interactive tool (TR/EN) + Academic thesis

### Mevcut Durum Analizi

**Research Phase: ✅ COMPLETE (100%)**
- 52 doküman analizi tamamlandı (~157,000 kelime)
- Academic foundation: PhD level (exceeds requirements)
- Algorithm selection: H-SAGA + NSGA-III validated
- Technology stack: M1-optimized Python stack identified
- Turkish context: Campus data, standards, regulations researched

**Implementation Phase: 🔴 NOT STARTED (0%)**
- No code written yet
- Dev environment not set up
- Git repository not initialized

### Kritik Kısıtlar
1. **Zaman:** 8 hafta (56 gün)
2. **Kaynak:** 1 developer (tek kişi)
3. **Donanım:** M1 MacBook Air (8GB RAM, 256GB SSD)
4. **Kapsam:** MVP only - full platform değil
5. **Akademik Teslim:** Documentation + defense slides gerekli

### Başarı Kriterleri (MVP)
✅ Çalışan web arayüzü (TR/EN)  
✅ 50-100 bina için optimizasyon (<2 dakika)  
✅ Road network generation (tensor fields)  
✅ 3+ objective optimization (cost, accessibility, adjacency)  
✅ Visual output (2D layout + metrics)  
✅ Demo video (5 dakika)  
✅ Academic documentation (thesis format)  
✅ Source code (GitHub, documented, MIT license)

---

## 💻 PART 1: TECHNOLOGY STACK (M1-OPTIMIZED)

### Core Backend Stack

**Python 3.11** (M1 native performance)
```bash
# Neden Python 3.11?
- M1 için optimize edilmiş
- NumPy/SciPy Apple Accelerate framework kullanır (3x hız)
- Rapid prototyping için ideal
- Rich AI/ML ecosystem
```

**Scientific Computing**
```python
numpy==1.26.2          # Apple Accelerate backend (CRITICAL for M1)
scipy==1.11.4          # Optimization algorithms
pandas==2.1.3          # Data manipulation
geopandas==0.14.1      # Geospatial operations
shapely==2.0.2         # Geometric operations
```

**Optimization Libraries**
```python
pymoo==0.6.1.1         # Multi-objective optimization (NSGA-III)
deap==1.4.1            # Genetic algorithms (backup)
```

**Geospatial**
```python
osmnx==1.9.0           # OpenStreetMap road networks
networkx==3.2.1        # Graph operations
rasterio==1.3.9        # Raster data (density maps)
folium==0.15.0         # Interactive maps
```

### Frontend Stack (Lightweight - M1 consideration)

**Option A: Streamlit (RECOMMENDED)**
```python
streamlit==1.29.0      # Rapid UI development
plotly==5.18.0         # Interactive visualizations
```

**Pros:**
- ✅ Python-native (no JS needed)
- ✅ Very fast development
- ✅ Low memory footprint (important for 8GB RAM)
- ✅ Built-in caching
- ✅ Easy deployment (Streamlit Cloud free tier)

**Cons:**
- ⚠️ Limited customization
- ⚠️ Not suitable for production (but fine for MVP/demo)

**Option B: Svelte + FastAPI (IF time permits - Week 7-8)**
```javascript
// frontend/
svelte==4.2.0          // Lightweight, fast compilation
vite==5.0.0            // M1-optimized build tool
```

```python
# backend/
fastapi==0.104.1       // Modern Python API framework
uvicorn==0.24.0        // ASGI server (async support)
```

**Decision:** Start with Streamlit (Week 1-6), optionally migrate to Svelte (Week 7) if ahead of schedule.

### Development Tools

**IDE: Cursor** (AI-powered, GPT-4 integration)
- ✅ Already have access
- ✅ Context-aware code generation
- ✅ Inline documentation generation
- ✅ Refactoring suggestions

**Version Control**
```bash
git==2.42.0
gh==2.38.0             # GitHub CLI
```

**Testing & Quality**
```python
pytest==7.4.3          # Unit testing
pytest-cov==4.1.0      # Coverage reports
black==23.11.0         # Code formatting (PEP 8)
flake8==6.1.0          # Linting
mypy==1.7.1            # Type checking
```

**Documentation**
```python
mkdocs==1.5.3          # Documentation site generator
mkdocs-material==9.5.0 # Material theme (beautiful)
```

### M1-Specific Optimizations

**1. NumPy Apple Accelerate**
```bash
# CRITICAL: Install NumPy with Accelerate backend
conda install numpy "libblas=*=*accelerate"

# Verify:
python -c "import numpy as np; np.__config__.show()"
# Should see: "accelerate" library
```

**2. Thread Configuration**
```python
import os
os.environ['OMP_NUM_THREADS'] = '4'  # M1's 4 performance cores
os.environ['NUMPY_NUM_THREADS'] = '4'
```

**3. Memory Management**
```python
# In-place operations (avoid copies on 8GB RAM)
array *= 2  # Good
array = array * 2  # Bad (creates copy)
```

**4. Vectorization (Utilize Apple Accelerate)**
```python
# Avoid Python loops
for i in range(1000):
    result[i] = calculate(data[i])  # SLOW

# Use NumPy vectorization
result = np.vectorize(calculate)(data)  # FAST (3-5x speedup)
```

### Expected Performance (M1 Air)

| Task | Time (Intel i7) | Time (M1 Air) | Speedup |
|------|----------------|---------------|---------|
| NumPy matrix ops | 120ms | 40ms | 3x |
| GA population eval (n=100) | 2.8s | 1.1s | 2.5x |
| Tensor field generation | 800ms | 300ms | 2.6x |
| Full optimization (50 buildings) | ~5min | ~2min | 2.5x |

---

## 🎓 PART 2: ACADEMIC CONTEXT & MVP SCOPE

### Academic Requirements (University Project)

**Deliverables:**
1. **Thesis Document** (TR - 60-80 pages)
   - Introduction & problem statement
   - Literature review (summarize 52 research docs)
   - Methodology (algorithms, architecture)
   - Implementation details
   - Case study (Turkish university campus)
   - Results & discussion
   - Conclusion & future work

2. **Defense Presentation** (TR - 20-30 slides)
   - Problem & motivation
   - Approach & innovation
   - Demo (live or video)
   - Results
   - Q&A preparation

3. **Source Code** (GitHub)
   - Clean, documented code
   - README (TR/EN)
   - MIT License
   - Installation guide

4. **Demo Video** (5-10 minutes, TR)
   - Problem introduction
   - UI walkthrough
   - Results visualization
   - Conclusion

### MVP Scope Definition (Critical - This determines 8 weeks)

**IN SCOPE (Must-Have for MVP)**

✅ **Core Optimization**
- H-SAGA algorithm implementation
- NSGA-III multi-objective optimization
- 3 objectives: Cost, Accessibility, Adjacency
- 50-100 building capacity
- <2 minute runtime

✅ **Spatial Features**
- Building placement optimization
- Tensor field-based road network generation
- Constraint handling (setbacks, min distances)

✅ **Data**
- Synthetic Turkish campus dataset (1 campus)
- Building typologies (5 types: residential, education, admin, health, social)
- Basic cost model

✅ **User Interface**
- Streamlit web app
- Turkish + English language toggle
- Interactive 2D map visualization (Folium)
- Metrics display (cost, accessibility scores)
- Export results (JSON, PNG)

✅ **Documentation**
- Thesis document (TR)
- README (TR/EN)
- Code comments (EN)
- User guide (TR)

**OUT OF SCOPE (Explicitly Excluded - Phase 2 / Future Work)**

❌ Real campus data integration (OSM import)  
❌ 3D visualization (Three.js)  
❌ Deep learning models (DRL, GNN)  
❌ Surrogate models for speedup  
❌ Multi-phase temporal planning  
❌ Energy/UHI simulation  
❌ Traffic simulation (SUMO)  
❌ BIM integration (IFC)  
❌ GIS software integration (QGIS export)  
❌ Cloud deployment  
❌ User authentication  
❌ Database backend  

**RATIONALE:**
- 8 weeks = 320 hours effective work time
- Core MVP needs ~250 hours
- Must leave 70 hours for documentation/defense prep
- Advanced features can be presented as "Future Work" in thesis

---

## 🤖 PART 3: AI TOOLS STRATEGIC USAGE PLAN

### Tool Arsenal

**1. ChatGPT Pro** (Deep research & complex explanations)
**2. Claude** (Code architecture & documentation)
**3. Gemini** (Deep research & multi-modal tasks)
**4. Cursor IDE** (Real-time coding assistance)
**5. GitHub Copilot** (Code completion)
**6. Google Colab Pro** (Computational experiments - if needed)

### AI Tools Allocation Matrix

| Sprint | Primary Tool | Usage | Specific Tasks |
|--------|--------------|-------|----------------|
| **Week 1** | Cursor + Copilot | Coding (80%) | Setup, H-SAGA core, tests |
| | Claude | Architecture (20%) | Design docs, code review |
| **Week 2** | Cursor + Copilot | Coding (70%) | Tensor fields, algorithms |
| | ChatGPT Pro | Research (20%) | Algorithm clarifications |
| | Claude | Documentation (10%) | Code comments, docstrings |
| **Week 3** | Cursor + Copilot | Coding (60%) | NSGA-III, constraints |
| | ChatGPT Pro | Debugging (30%) | Complex algorithm issues |
| | Gemini | Testing (10%) | Test case generation |
| **Week 4** | Cursor + Copilot | Coding (70%) | UI development (Streamlit) |
| | Claude | UX (20%) | Interface design guidance |
| | ChatGPT Pro | Turkish localization (10%) | Translation review |
| **Week 5** | Cursor + Copilot | Coding (50%) | Integration, bug fixes |
| | ChatGPT Pro | Optimization (30%) | Performance debugging |
| | Colab Pro | Experiments (20%) | Benchmark comparisons |
| **Week 6** | ChatGPT Pro | Documentation (40%) | Thesis drafting (TR) |
| | Claude | Documentation (40%) | README, technical docs |
| | Cursor | Polish (20%) | Code refactoring |
| **Week 7** | ChatGPT Pro | Documentation (60%) | Thesis completion |
| | Gemini | Visuals (30%) | Diagrams, figures |
| | Claude | Translation (10%) | EN documentation |
| **Week 8** | ChatGPT Pro | Presentation (50%) | Defense slides |
| | Claude | Review (30%) | Document proofreading |
| | Cursor | Demo prep (20%) | Bug fixes, polish |

### Detailed AI Tool Usage Strategies

#### **Cursor IDE (Code Generation)**

**When to Use:**
- Writing new functions/classes
- Implementing algorithms from papers
- Refactoring existing code
- Generating unit tests

**Best Practices:**
```python
# 1. Provide context in comments
# CONTEXT: Implementing H-SAGA from Li et al. 2025
# INPUT: List of Building objects, spatial constraints
# OUTPUT: Optimized building positions
# ALGORITHM: SA (200 iter) → GA (100 gen)
def optimize_layout(buildings, constraints):
    # Cursor will generate high-quality code with this context
    pass

# 2. Use inline prompts (Cmd+K)
# "implement simulated annealing with adaptive cooling schedule"

# 3. Ask for explanations (Cmd+L in chat)
# "explain why mutation rate is 0.15 in this GA"
```

#### **ChatGPT Pro (Research & Complex Problems)**

**When to Use:**
- Understanding complex algorithms from papers
- Debugging non-obvious errors
- Writing thesis sections
- Generating test datasets

**Prompt Templates:**
```
[Algorithm Understanding]
"I'm implementing H-SAGA from Li et al. 2025. The paper says:
[paste excerpt]. Can you explain in detail how the 'elite
preservation + diversity injection' step works, with Python pseudocode?"

[Debugging]
"My NSGA-III is converging too slowly. Here's my code: [paste].
Here's the convergence plot: [image]. What could be wrong?"

[Thesis Writing]
"Write the 'Multi-Objective Optimization' section of my thesis.
Context: [background]. Requirements: Academic tone, 2-3 pages,
include mathematical formulation, cite pymoo library."
```

#### **Claude (Architecture & Documentation)**

**When to Use:**
- System architecture design
- Writing READMEs, API docs
- Code review and refactoring suggestions
- Generating comprehensive documentation

**Prompt Templates:**
```
[Architecture Review]
"Review this class diagram for PlanifyAI. Does it follow
SOLID principles? Suggest improvements for testability."

[Documentation]
"Generate a comprehensive README for this repository.
Include: installation, quick start, architecture overview,
API reference, examples. Tone: professional but friendly."

[Code Review]
"Review this module for: 1) M1 optimization opportunities,
2) memory efficiency, 3) code style (PEP 8), 4) test coverage gaps."
```

#### **Gemini (Deep Research & Multi-Modal)**

**When to Use:**
- Extended research queries (when GPT Deep Research used up)
- Generating diagrams from descriptions
- Analyzing visual outputs (plots, maps)
- Comparative analysis tasks

**Use Cases:**
- "Generate architecture diagram from this description: [text]"
- "Analyze this convergence plot. Is the algorithm stuck in local optima?"
- "Compare H-SAGA vs pure GA: create a comparison table with metrics"

#### **Google Colab Pro (Computational Experiments)**

**When to Use:**
- Running benchmarks (if M1 Mac is busy)
- Training surrogate models (future work)
- Parallel experiments (comparing algorithms)

**Setup:**
```python
# Colab notebook for benchmark comparisons
# Compare: Pure GA, Pure SA, H-SAGA, NSGA-II, NSGA-III
# Dataset: 50 buildings, 5 runs each
# Metrics: Convergence speed, solution quality, runtime
```

---

## 📆 PART 4: 8-WEEK SPRINT PLAN (DETAILED)

### Sprint Overview Table

| Hafta | Modül / Hedef | Ana Görevler | Kullanılacak Araçlar | Üretilecek Çıktılar |
|-------|---------------|--------------|---------------------|---------------------|
| **Week 1** | Setup & Core Algorithm | Dev env setup, H-SAGA implementation, unit tests | Cursor, Copilot, Claude (design) | Working H-SAGA, 80%+ test coverage |
| **Week 2** | Spatial Features | Tensor fields, road generation, constraints | Cursor, Copilot, ChatGPT (research) | Road network generator, constraint engine |
| **Week 3** | Multi-Objective Optimization | NSGA-III integration, fitness functions, benchmark | Cursor, ChatGPT (debug), Colab (tests) | Working MOO, benchmark results |
| **Week 4** | User Interface | Streamlit app, visualizations, TR/EN toggle | Cursor, Claude (UX), ChatGPT (i18n) | Interactive web demo |
| **Week 5** | Integration & Testing | End-to-end integration, bug fixes, performance tuning | Cursor, ChatGPT (optimization), Colab | Stable MVP, performance report |
| **Week 6** | Documentation (Code) | README, API docs, code comments, user guide | Claude (docs), ChatGPT (TR writing), Cursor (cleanup) | Complete documentation |
| **Week 7** | Thesis Writing | Draft chapters, methodology, results sections | ChatGPT Pro (writing), Gemini (figures), Claude (review) | Thesis draft (80%+) |
| **Week 8** | Finalization & Defense | Thesis finalization, defense slides, demo video, rehearsal | ChatGPT (slides), Claude (proofread), Cursor (demo polish) | Final submission package |

---

### **WEEK 1: SETUP & CORE ALGORITHM**

**Dates:** Nov 4-10 (Mon-Sun)  
**Goal:** Working H-SAGA implementation + dev environment  
**Effort:** 40 hours (5-6 hours/day)

#### Monday (Nov 4): Environment Setup

**Morning (3h): Development Environment**
```bash
# 1. System setup (M1 specific)
xcode-select --install
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install python@3.11 git gh

# 2. Project structure
mkdir planifyai && cd planifyai
git init
git checkout -b develop

# Create folder structure
mkdir -p src/{algorithms,spatial,data,ui,utils}
mkdir -p tests/{unit,integration,benchmarks}
mkdir -p docs/{api,thesis,user-guide}
mkdir -p data/{raw,processed,outputs}
mkdir -p config
mkdir notebooks

# 3. Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# 4. Install core dependencies
pip install numpy scipy pandas geopandas shapely
pip install pymoo networkx osmnx
pip install pytest pytest-cov black flake8 mypy

# CRITICAL: Verify NumPy uses Accelerate
python -c "import numpy as np; np.__config__.show()"
```

**Afternoon (3h): Project Configuration**
```bash
# 1. Create pyproject.toml
cat > pyproject.toml << EOF
[build-system]
requires = ["setuptools>=65.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "planifyai"
version = "0.1.0"
description = "AI-powered generative spatial planning"
authors = [{name = "Your Name", email = "your.email@edu.tr"}]
license = {text = "MIT"}
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.26.0",
    "scipy>=1.11.0",
    "pandas>=2.1.0",
    "geopandas>=0.14.0",
    "shapely>=2.0.0",
    "pymoo>=0.6.0",
    "networkx>=3.2.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.4", "pytest-cov>=4.1", "black>=23.11", "mypy>=1.7"]
ui = ["streamlit>=1.29", "plotly>=5.18", "folium>=0.15"]
EOF

# 2. Create .gitignore
cat > .gitignore << EOF
# Python
venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage

# IDE
.vscode/
.cursor/
.idea/

# Data
data/raw/*
!data/raw/.gitkeep
outputs/*.png
outputs/*.json

# System
.DS_Store
EOF

# 3. Initialize git
git add .
git commit -m "chore: initial project structure"

# 4. Create GitHub repo (if not exists)
gh repo create planifyai --public --source=. --remote=origin
git push -u origin develop
```

**Tools Used:** Terminal, Cursor, gh CLI

#### Tuesday-Thursday (Nov 5-7): H-SAGA Implementation

**Day 2 (6h): H-SAGA Core**

```python
# src/algorithms/hsaga.py
"""
Hybrid Simulated Annealing - Genetic Algorithm (H-SAGA)
Based on Li et al. (2025) - Reverse hybrid approach
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict, Callable
import numpy as np
from enum import Enum

class BuildingType(Enum):
    RESIDENTIAL = "residential"
    EDUCATIONAL = "educational"
    ADMINISTRATIVE = "administrative"
    HEALTH = "health"
    SOCIAL = "social"

@dataclass
class Building:
    """Building entity with spatial requirements"""
    id: str
    type: BuildingType
    area: float  # m²
    floors: int
    position: Tuple[float, float] = None  # (x, y) in meters
    
    @property
    def footprint(self) -> float:
        """Ground floor footprint"""
        return self.area / self.floors

class Constraint:
    """Spatial constraint definition"""
    def __init__(self, constraint_type: str, params: Dict):
        self.type = constraint_type
        self.params = params
    
    def check(self, solution: List[Building]) -> bool:
        """Check if solution satisfies constraint"""
        if self.type == "min_distance":
            # Check minimum distance between buildings
            for i, b1 in enumerate(solution):
                for b2 in solution[i+1:]:
                    dist = np.linalg.norm(
                        np.array(b1.position) - np.array(b2.position)
                    )
                    if dist < self.params["threshold"]:
                        return False
            return True
        elif self.type == "site_boundary":
            # Check all buildings within site bounds
            bounds = self.params["bounds"]  # (xmin, ymin, xmax, ymax)
            for b in solution:
                if not (bounds[0] <= b.position[0] <= bounds[2] and
                        bounds[1] <= b.position[1] <= bounds[3]):
                    return False
            return True
        else:
            raise ValueError(f"Unknown constraint type: {self.type}")

class HSAGA:
    """
    Hybrid SA→GA optimization for spatial planning
    Stage 1: SA for global exploration (200 iterations)
    Stage 2: GA for local refinement (100 generations)
    """
    
    def __init__(self,
                 buildings: List[Building],
                 site_bounds: Tuple[float, float, float, float],
                 constraints: List[Constraint],
                 objectives: List[Callable]):
        self.buildings = buildings
        self.bounds = site_bounds  # (xmin, ymin, xmax, ymax)
        self.constraints = constraints
        self.objectives = objectives
        
        # SA parameters (Li et al.)
        self.sa_temp_init = 300
        self.sa_cooling_rate = 0.95
        self.sa_iterations = 200
        
        # GA parameters
        self.ga_pop_size = 100
        self.ga_generations = 100
        self.ga_crossover_rate = 0.8
        self.ga_mutation_rate = 0.15  # High for diversity
        
        self.history = {
            'sa_fitness': [],
            'ga_fitness': [],
            'best_solution': None,
            'runtime': 0
        }
    
    def optimize(self) -> Dict:
        """Main optimization pipeline"""
        import time
        start_time = time.time()
        
        print("🔥 Stage 1: Simulated Annealing (global exploration)")
        sa_solutions = self._simulated_annealing()
        
        print("🧬 Stage 2: Genetic Algorithm (local refinement)")
        refined_solutions = self._genetic_algorithm(sa_solutions)
        
        # Select best solution
        best = min(refined_solutions, key=lambda s: s['fitness'])
        self.history['best_solution'] = best
        self.history['runtime'] = time.time() - start_time
        
        print(f"✅ Optimization complete in {self.history['runtime']:.1f}s")
        return best
    
    def _simulated_annealing(self) -> List[Dict]:
        """SA for global exploration - multiple parallel chains"""
        solutions = []
        
        for chain in range(10):  # 10 parallel SA chains
            # Random initial solution
            current = self._random_solution()
            current_fitness = self._evaluate(current)
            best = current.copy()
            best_fitness = current_fitness
            
            temp = self.sa_temp_init
            
            for iteration in range(self.sa_iterations):
                # Generate neighbor (perturbation)
                neighbor = self._perturbation(current)
                neighbor_fitness = self._evaluate(neighbor)
                
                # Acceptance criterion
                delta = neighbor_fitness - current_fitness
                if delta < 0 or np.random.rand() < np.exp(-delta / temp):
                    current = neighbor
                    current_fitness = neighbor_fitness
                    
                    if current_fitness < best_fitness:
                        best = current.copy()
                        best_fitness = current_fitness
                
                # Cool down
                temp *= self.sa_cooling_rate
            
            solutions.append({
                'solution': best,
                'fitness': best_fitness
            })
            self.history['sa_fitness'].append(best_fitness)
        
        return solutions
    
    def _genetic_algorithm(self, initial_population: List[Dict]) -> List[Dict]:
        """GA for local refinement"""
        # Initialize population with SA solutions + random individuals
        population = initial_population.copy()
        while len(population) < self.ga_pop_size:
            population.append({
                'solution': self._random_solution(),
                'fitness': None
            })
        
        # Evaluate initial population
        for ind in population:
            if ind['fitness'] is None:
                ind['fitness'] = self._evaluate(ind['solution'])
        
        for generation in range(self.ga_generations):
            # Selection (tournament)
            parents = self._tournament_selection(population, k=3)
            
            # Crossover
            offspring = []
            for i in range(0, len(parents), 2):
                if i+1 < len(parents):
                    child1, child2 = self._crossover(
                        parents[i]['solution'], 
                        parents[i+1]['solution']
                    )
                    offspring.append({'solution': child1, 'fitness': None})
                    offspring.append({'solution': child2, 'fitness': None})
            
            # Mutation
            for ind in offspring:
                if np.random.rand() < self.ga_mutation_rate:
                    ind['solution'] = self._mutate(ind['solution'])
            
            # Evaluate offspring
            for ind in offspring:
                ind['fitness'] = self._evaluate(ind['solution'])
            
            # Elitism + diversity injection (Li et al.)
            population.sort(key=lambda x: x['fitness'])
            elite = population[:10]  # Top 10%
            diverse = self._diversity_injection(offspring, n=10)
            population = elite + diverse + offspring[:self.ga_pop_size-20]
            
            best_fitness = population[0]['fitness']
            self.history['ga_fitness'].append(best_fitness)
        
        return population
    
    def _random_solution(self) -> List[Building]:
        """Generate random valid solution"""
        solution = []
        for b in self.buildings:
            b_copy = Building(
                id=b.id,
                type=b.type,
                area=b.area,
                floors=b.floors,
                position=(
                    np.random.uniform(self.bounds[0], self.bounds[2]),
                    np.random.uniform(self.bounds[1], self.bounds[3])
                )
            )
            solution.append(b_copy)
        
        # Repair if violates constraints
        max_attempts = 100
        for _ in range(max_attempts):
            if all(c.check(solution) for c in self.constraints):
                break
            # Re-randomize positions
            for b in solution:
                b.position = (
                    np.random.uniform(self.bounds[0], self.bounds[2]),
                    np.random.uniform(self.bounds[1], self.bounds[3])
                )
        
        return solution
    
    def _evaluate(self, solution: List[Building]) -> float:
        """Evaluate fitness (lower is better)"""
        # Weighted sum of objectives
        total_fitness = 0.0
        for obj_func in self.objectives:
            total_fitness += obj_func(solution)
        return total_fitness
    
    def _perturbation(self, solution: List[Building]) -> List[Building]:
        """Small random perturbation for SA"""
        new_solution = [Building(b.id, b.type, b.area, b.floors, b.position) 
                       for b in solution]
        
        # Perturb one random building
        idx = np.random.randint(len(new_solution))
        b = new_solution[idx]
        
        # Small random move
        delta = 20  # meters
        new_x = b.position[0] + np.random.uniform(-delta, delta)
        new_y = b.position[1] + np.random.uniform(-delta, delta)
        
        # Clip to bounds
        new_x = np.clip(new_x, self.bounds[0], self.bounds[2])
        new_y = np.clip(new_y, self.bounds[1], self.bounds[3])
        
        b.position = (new_x, new_y)
        return new_solution
    
    def _tournament_selection(self, population: List[Dict], k: int) -> List[Dict]:
        """Tournament selection"""
        selected = []
        for _ in range(len(population)):
            tournament = np.random.choice(population, size=k, replace=False)
            winner = min(tournament, key=lambda x: x['fitness'])
            selected.append(winner)
        return selected
    
    def _crossover(self, parent1: List[Building], parent2: List[Building]) -> Tuple:
        """Single-point crossover"""
        n = len(parent1)
        point = np.random.randint(1, n)
        
        child1 = ([Building(b.id, b.type, b.area, b.floors, b.position) 
                  for b in parent1[:point]] +
                 [Building(b.id, b.type, b.area, b.floors, b.position) 
                  for b in parent2[point:]])
        
        child2 = ([Building(b.id, b.type, b.area, b.floors, b.position) 
                  for b in parent2[:point]] +
                 [Building(b.id, b.type, b.area, b.floors, b.position) 
                  for b in parent1[point:]])
        
        return child1, child2
    
    def _mutate(self, solution: List[Building]) -> List[Building]:
        """Random mutation"""
        new_solution = [Building(b.id, b.type, b.area, b.floors, b.position) 
                       for b in solution]
        
        # Mutate 1-3 random buildings
        n_mutate = np.random.randint(1, 4)
        indices = np.random.choice(len(new_solution), size=n_mutate, replace=False)
        
        for idx in indices:
            b = new_solution[idx]
            b.position = (
                np.random.uniform(self.bounds[0], self.bounds[2]),
                np.random.uniform(self.bounds[1], self.bounds[3])
            )
        
        return new_solution
    
    def _diversity_injection(self, population: List[Dict], n: int) -> List[Dict]:
        """Inject diverse solutions (Li et al.)"""
        # Select n most diverse solutions based on position variance
        positions = [np.array([b.position for b in ind['solution']]) 
                    for ind in population]
        variances = [np.var(pos) for pos in positions]
        
        # Get indices of top n variance
        diverse_indices = np.argsort(variances)[-n:]
        return [population[i] for i in diverse_indices]
```

**Tools:** Cursor (code generation), Copilot (autocomplete), Claude (algorithm review)

**Day 3 (6h): Objective Functions**

```python
# src/algorithms/objectives.py
"""
Objective functions for campus planning optimization
"""

import numpy as np
from typing import List
from .hsaga import Building, BuildingType

def minimize_cost(solution: List[Building]) -> float:
    """
    Objective 1: Minimize construction cost
    Simple cost model based on area and building type
    """
    cost_per_sqm = {
        BuildingType.RESIDENTIAL: 1500,  # TL/m²
        BuildingType.EDUCATIONAL: 2000,
        BuildingType.ADMINISTRATIVE: 1800,
        BuildingType.HEALTH: 2500,
        BuildingType.SOCIAL: 1600,
    }
    
    total_cost = sum(b.area * cost_per_sqm[b.type] for b in solution)
    
    # Normalize to [0, 1] range for fair weighting
    max_cost = 100_000_000  # 100M TL reference
    return total_cost / max_cost

def minimize_walking_distance(solution: List[Building]) -> float:
    """
    Objective 2: Minimize average walking distance
    Focus on residential-to-educational connections
    """
    residential = [b for b in solution if b.type == BuildingType.RESIDENTIAL]
    educational = [b for b in solution if b.type == BuildingType.EDUCATIONAL]
    
    if not residential or not educational:
        return 0.0
    
    total_distance = 0.0
    count = 0
    
    for res in residential:
        for edu in educational:
            dist = np.linalg.norm(
                np.array(res.position) - np.array(edu.position)
            )
            total_distance += dist
            count += 1
    
    avg_distance = total_distance / count if count > 0 else 0
    
    # Normalize: ideal distance ~200m, max acceptable ~800m
    normalized = (avg_distance - 200) / 600
    return np.clip(normalized, 0, 1)

def maximize_adjacency_satisfaction(solution: List[Building]) -> float:
    """
    Objective 3: Maximize adjacency matrix satisfaction
    Negative objective (minimize dissatisfaction)
    """
    # Adjacency matrix (from research)
    adjacency = {
        (BuildingType.RESIDENTIAL, BuildingType.EDUCATIONAL): 5,
        (BuildingType.RESIDENTIAL, BuildingType.SOCIAL): 4,
        (BuildingType.RESIDENTIAL, BuildingType.HEALTH): -3,
        (BuildingType.EDUCATIONAL, BuildingType.ADMINISTRATIVE): 3,
        (BuildingType.EDUCATIONAL, BuildingType.SOCIAL): 2,
        (BuildingType.HEALTH, BuildingType.HEALTH): -5,  # Separate clinics
    }
    
    total_satisfaction = 0.0
    max_satisfaction = 0.0
    
    for i, b1 in enumerate(solution):
        for b2 in solution[i+1:]:
            key = tuple(sorted([b1.type, b2.type]))
            weight = adjacency.get(key, 0)
            
            if weight != 0:
                dist = np.linalg.norm(
                    np.array(b1.position) - np.array(b2.position)
                )
                
                # High adjacency want close, negative want far
                if weight > 0:
                    satisfaction = weight / (1 + dist / 100)  # Closer is better
                else:
                    satisfaction = abs(weight) * (dist / 100)  # Farther is better
                
                total_satisfaction += satisfaction
                max_satisfaction += abs(weight)
    
    # Return dissatisfaction (to minimize)
    return 1 - (total_satisfaction / max_satisfaction if max_satisfaction > 0 else 0)
```

**Day 4 (6h): Unit Tests**

```python
# tests/unit/test_hsaga.py
"""
Unit tests for H-SAGA implementation
Target: 80%+ code coverage
"""

import pytest
import numpy as np
from src.algorithms.hsaga import (
    Building, BuildingType, Constraint, HSAGA
)
from src.algorithms.objectives import (
    minimize_cost, 
    minimize_walking_distance,
    maximize_adjacency_satisfaction
)

class TestBuilding:
    """Test Building dataclass"""
    
    def test_building_creation(self):
        b = Building(
            id="B1",
            type=BuildingType.RESIDENTIAL,
            area=5000,
            floors=4,
            position=(100, 100)
        )
        assert b.footprint == 1250  # 5000 / 4
    
    def test_building_without_position(self):
        b = Building("B2", BuildingType.EDUCATIONAL, 3000, 3)
        assert b.position is None

class TestConstraints:
    """Test constraint checking"""
    
    def test_min_distance_constraint(self):
        c = Constraint("min_distance", {"threshold": 50})
        
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 1000, 2, (0, 0)),
            Building("B2", BuildingType.EDUCATIONAL, 1000, 2, (100, 0)),
        ]
        
        assert c.check(buildings) == True  # 100m apart > 50m
        
        buildings[1].position = (30, 0)  # Move closer
        assert c.check(buildings) == False  # 30m < 50m
    
    def test_site_boundary_constraint(self):
        c = Constraint("site_boundary", {"bounds": (0, 0, 1000, 1000)})
        
        buildings = [
            Building("B1", BuildingType.RESIDENTIAL, 1000, 2, (500, 500)),
        ]
        assert c.check(buildings) == True
        
        buildings[0].position = (1100, 500)  # Outside boundary
        assert c.check(buildings) == False

class TestObjectives:
    """Test objective functions"""
    
    def test_cost_objective(self):
        solution = [
            Building("B1", BuildingType.RESIDENTIAL, 5000, 2, (0, 0)),
            Building("B2", BuildingType.EDUCATIONAL, 3000, 2, (100, 0)),
        ]
        
        cost = minimize_cost(solution)
        assert 0 <= cost <= 1  # Normalized
        assert cost > 0  # Non-zero
    
    def test_walking_distance(self):
        solution = [
            Building("R1", BuildingType.RESIDENTIAL, 1000, 2, (0, 0)),
            Building("E1", BuildingType.EDUCATIONAL, 1000, 2, (200, 0)),
        ]
        
        distance = minimize_walking_distance(solution)
        assert 0 <= distance <= 1
        
        # Test edge case: no residential buildings
        solution_no_res = [
            Building("E1", BuildingType.EDUCATIONAL, 1000, 2, (0, 0)),
        ]
        assert minimize_walking_distance(solution_no_res) == 0.0

class TestHSAGA:
    """Integration tests for H-SAGA"""
    
    @pytest.fixture
    def simple_problem(self):
        """Simple 5-building problem"""
        buildings = [
            Building(f"B{i}", 
                    np.random.choice(list(BuildingType)),
                    np.random.randint(1000, 5000),
                    np.random.randint(2, 5))
            for i in range(5)
        ]
        
        constraints = [
            Constraint("min_distance", {"threshold": 30}),
            Constraint("site_boundary", {"bounds": (0, 0, 500, 500)}),
        ]
        
        objectives = [
            minimize_cost,
            minimize_walking_distance,
            maximize_adjacency_satisfaction,
        ]
        
        return buildings, constraints, objectives
    
    def test_random_solution_generation(self, simple_problem):
        buildings, constraints, objectives = simple_problem
        optimizer = HSAGA(buildings, (0, 0, 500, 500), constraints, objectives)
        
        solution = optimizer._random_solution()
        
        assert len(solution) == len(buildings)
        for b in solution:
            assert b.position is not None
            assert 0 <= b.position[0] <= 500
            assert 0 <= b.position[1] <= 500
    
    def test_full_optimization_run(self, simple_problem):
        """End-to-end test (may take ~30 seconds)"""
        buildings, constraints, objectives = simple_problem
        
        # Reduce iterations for faster testing
        optimizer = HSAGA(buildings, (0, 0, 500, 500), constraints, objectives)
        optimizer.sa_iterations = 20  # Reduced from 200
        optimizer.ga_generations = 10  # Reduced from 100
        
        result = optimizer.optimize()
        
        assert result is not None
        assert 'solution' in result
        assert 'fitness' in result
        assert optimizer.history['runtime'] > 0
        
        # Check solution validity
        solution = result['solution']
        assert all(c.check(solution) for c in constraints)

# Run with: pytest tests/unit/test_hsaga.py -v --cov=src
```

**Tools:** Cursor (test generation), pytest, pytest-cov

**Deliverables (Week 1):**
- ✅ Working H-SAGA implementation (~400 lines)
- ✅ 3 objective functions
- ✅ Constraint system
- ✅ Unit tests (80%+ coverage)
- ✅ Git commits with conventional commits
- ✅ Dev environment fully set up

**Git Commits:**
```bash
git add .
git commit -m "feat: implement H-SAGA core algorithm

- SA→GA hybrid optimization
- Building and constraint dataclasses
- Random solution generation
- Perturbation, crossover, mutation operators
- Diversity injection mechanism

Based on Li et al. (2025)"

git commit -m "feat: add objective functions

- minimize_cost: construction cost model
- minimize_walking_distance: residential-educational
- maximize_adjacency_satisfaction: QAP-inspired

Ref: Building Typology research doc"

git commit -m "test: add H-SAGA unit tests

- 80%+ code coverage
- Test fixtures for problems
- Edge case handling
- Integration test for full optimization run"

git push origin develop
```

---

### **WEEK 2: SPATIAL FEATURES**

**Dates:** Nov 11-17  
**Goal:** Tensor field road generation + spatial constraints  
**Effort:** 40 hours

#### Overview
- Implement semantic tensor fields (patent-worthy component!)
- RK4 streamline integration for road network
- Spatial constraint engine (setbacks, exclusion zones)
- Integration with H-SAGA

#### Monday-Tuesday: Tensor Field Theory

```python
# src/spatial/tensor_fields.py
"""
Semantic tensor field generation for road networks
PATENT OPPORTUNITY: Dynamic feedback with MOO
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import List, Tuple
from ..algorithms.hsaga import Building, BuildingType

class TensorFieldGenerator:
    """
    Generate tensor fields from building layout
    Each building type contributes different field patterns:
    - Residential: Radial attraction
    - Educational: Grid-aligned
    - Commercial: Radial + high connectivity
    """
    
    def __init__(self, grid_size: int = 200, cell_size: float = 5.0):
        """
        Args:
            grid_size: Number of grid cells per dimension
            cell_size: Real-world size of each cell (meters)
        """
        self.grid_size = grid_size
        self.cell_size = cell_size
        self.tensor_field = None
        
        # Field parameters per building type
        self.type_params = {
            BuildingType.RESIDENTIAL: {
                'pattern': 'radial',
                'influence_radius': 200,  # meters
                'strength': 0.8
            },
            BuildingType.EDUCATIONAL: {
                'pattern': 'grid',
                'influence_radius': 300,
                'strength': 1.0
            },
            BuildingType.COMMERCIAL: {
                'pattern': 'radial',
                'influence_radius': 400,
                'strength': 1.2
            },
            BuildingType.HEALTH: {
                'pattern': 'radial',
                'influence_radius': 250,
                'strength': 0.9
            },
            BuildingType.SOCIAL: {
                'pattern': 'radial',
                'influence_radius': 180,
                'strength': 0.7
            },
        }
    
    def generate(self, buildings: List[Building]) -> np.ndarray:
        """
        Generate 2x2 symmetric tensor field
        Returns: (grid_size, grid_size, 2, 2) tensor field
        """
        # Initialize tensor field
        Txx = np.zeros((self.grid_size, self.grid_size))
        Tyy = np.zeros((self.grid_size, self.grid_size))
        Txy = np.zeros((self.grid_size, self.grid_size))
        
        # Accumulate contributions from each building
        for building in buildings:
            if building.position is None:
                continue
            
            params = self.type_params[building.type]
            
            if params['pattern'] == 'radial':
                contrib = self._radial_field(building, params)
            elif params['pattern'] == 'grid':
                contrib = self._grid_field(building, params)
            else:
                raise ValueError(f"Unknown pattern: {params['pattern']}")
            
            # Accumulate (weighted sum)
            Txx += contrib['Txx']
            Tyy += contrib['Tyy']
            Txy += contrib['Txy']
        
        # Smooth the field (reduce noise)
        Txx = gaussian_filter(Txx, sigma=2.0)
        Tyy = gaussian_filter(Tyy, sigma=2.0)
        Txy = gaussian_filter(Txy, sigma=2.0)
        
        # Construct 2x2 tensor at each grid point
        tensor_field = np.zeros((self.grid_size, self.grid_size, 2, 2))
        tensor_field[:, :, 0, 0] = Txx
        tensor_field[:, :, 1, 1] = Tyy
        tensor_field[:, :, 0, 1] = Txy
        tensor_field[:, :, 1, 0] = Txy  # Symmetric
        
        self.tensor_field = tensor_field
        return tensor_field
    
    def _radial_field(self, building: Building, params: Dict) -> Dict:
        """Generate radial tensor field around a point"""
        Txx = np.zeros((self.grid_size, self.grid_size))
        Tyy = np.zeros((self.grid_size, self.grid_size))
        Txy = np.zeros((self.grid_size, self.grid_size))
        
        # Building position in grid coordinates
        bx_grid = int(building.position[0] / self.cell_size)
        by_grid = int(building.position[1] / self.cell_size)
        
        radius_cells = int(params['influence_radius'] / self.cell_size)
        strength = params['strength']
        
        # Create meshgrid
        y_idx, x_idx = np.ogrid[:self.grid_size, :self.grid_size]
        
        # Distance from building
        dx = (x_idx - bx_grid) * self.cell_size
        dy = (y_idx - by_grid) * self.cell_size
        distance = np.sqrt(dx**2 + dy**2)
        
        # Decay function
        influence = np.exp(-distance / params['influence_radius'])
        influence *= strength
        
        # Radial tensor: aligned with direction from building
        angle = np.arctan2(dy, dx)
        Txx = influence * np.cos(angle)**2
        Tyy = influence * np.sin(angle)**2
        Txy = influence * np.sin(angle) * np.cos(angle)
        
        return {'Txx': Txx, 'Tyy': Tyy, 'Txy': Txy}
    
    def _grid_field(self, building: Building, params: Dict) -> Dict:
        """Generate grid-aligned tensor field"""
        Txx = np.ones((self.grid_size, self.grid_size))
        Tyy = np.ones((self.grid_size, self.grid_size))
        Txy = np.zeros((self.grid_size, self.grid_size))
        
        # Apply influence decay
        bx_grid = int(building.position[0] / self.cell_size)
        by_grid = int(building.position[1] / self.cell_size)
        
        y_idx, x_idx = np.ogrid[:self.grid_size, :self.grid_size]
        dx = (x_idx - bx_grid) * self.cell_size
        dy = (y_idx - by_grid) * self.cell_size
        distance = np.sqrt(dx**2 + dy**2)
        
        influence = np.exp(-distance / params['influence_radius'])
        influence *= params['strength']
        
        Txx *= influence
        Tyy *= influence
        
        return {'Txx': Txx, 'Tyy': Tyy, 'Txy': Txy}
    
    def compute_eigenvectors(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute major eigenvector field (road direction)
        Returns: (evec_x, evec_y) arrays
        """
        if self.tensor_field is None:
            raise ValueError("Must call generate() first")
        
        # Eigendecomposition at each grid point
        eigenvalues = np.zeros((self.grid_size, self.grid_size, 2))
        eigenvectors = np.zeros((self.grid_size, self.grid_size, 2, 2))
        
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                tensor = self.tensor_field[i, j]
                evals, evecs = np.linalg.eigh(tensor)
                
                # Sort by magnitude (major eigenvector)
                idx = np.argsort(np.abs(evals))[::-1]
                eigenvalues[i, j] = evals[idx]
                eigenvectors[i, j] = evecs[:, idx]
        
        # Extract major eigenvector field
        evec_x = eigenvectors[:, :, 0, 0]
        evec_y = eigenvectors[:, :, 1, 0]
        
        return evec_x, evec_y
```

#### Wednesday-Thursday: RK4 Streamline Integration

```python
# src/spatial/streamlines.py
"""
Adaptive RK4 streamline integration for road generation
"""

import numpy as np
from typing import List, Tuple
from .tensor_fields import TensorFieldGenerator

class StreamlineIntegrator:
    """
    Generate road network by tracing streamlines in tensor field
    Uses adaptive step size for smooth curves
    """
    
    def __init__(self, 
                 tensor_generator: TensorFieldGenerator,
                 step_size_init: float = 5.0,
                 min_step: float = 1.0,
                 max_step: float = 20.0):
        self.tensor_gen = tensor_generator
        self.step_size_init = step_size_init
        self.min_step = min_step
        self.max_step = max_step
        
        # Get eigenvector field
        self.evec_x, self.evec_y = tensor_generator.compute_eigenvectors()
    
    def trace_streamline(self, 
                        start_point: Tuple[float, float],
                        max_length: float = 500,
                        direction: int = 1) -> List[Tuple[float, float]]:
        """
        Trace a single streamline using adaptive RK4
        
        Args:
            start_point: (x, y) in meters
            max_length: Maximum road length
            direction: 1 for forward, -1 for backward
        
        Returns:
            List of (x, y) points forming the road
        """
        points = [start_point]
        current_point = np.array(start_point, dtype=float)
        step_size = self.step_size_init
        total_length = 0
        
        while total_length < max_length:
            # RK4 integration step
            new_point, error = self._rk4_step(current_point, step_size, direction)
            
            # Adaptive step size control
            if error < 0.1:  # Low error - increase step
                step_size = min(step_size * 1.5, self.max_step)
            elif error > 0.5:  # High error - decrease step
                step_size = max(step_size * 0.5, self.min_step)
                continue  # Retry with smaller step
            
            # Check bounds
            if not self._in_bounds(new_point):
                break
            
            # Add point
            points.append(tuple(new_point))
            
            # Update
            segment_length = np.linalg.norm(new_point - current_point)
            total_length += segment_length
            current_point = new_point
            
            # Stop if curvature too high (sharp turn)
            if len(points) >= 3:
                curvature = self._compute_curvature(points[-3:])
                if curvature > 0.1:  # Max curvature threshold
                    break
        
        return points
    
    def _rk4_step(self, 
                  point: np.ndarray, 
                  h: float,
                  direction: int) -> Tuple[np.ndarray, float]:
        """
        4th-order Runge-Kutta integration step
        Returns: (new_point, error_estimate)
        """
        # Get eigenvector at current point
        v1 = direction * self._get_eigenvector_at(point)
        
        # RK4 intermediate points
        k1 = v1
        k2 = direction * self._get_eigenvector_at(point + 0.5 * h * k1)
        k3 = direction * self._get_eigenvector_at(point + 0.5 * h * k2)
        k4 = direction * self._get_eigenvector_at(point + h * k3)
        
        # Weighted average
        new_point = point + (h / 6) * (k1 + 2*k2 + 2*k3 + k4)
        
        # Error estimate (difference between 4th and 2nd order)
        new_point_euler = point + h * v1  # 1st order
        error = np.linalg.norm(new_point - new_point_euler)
        
        return new_point, error
    
    def _get_eigenvector_at(self, point: np.ndarray) -> np.ndarray:
        """Get normalized eigenvector at point (bilinear interpolation)"""
        # Convert to grid coordinates
        i = point[0] / self.tensor_gen.cell_size
        j = point[1] / self.tensor_gen.cell_size
        
        # Bilinear interpolation
        i0, j0 = int(np.floor(i)), int(np.floor(j))
        i1, j1 = i0 + 1, j0 + 1
        
        # Clip to grid bounds
        i0 = np.clip(i0, 0, self.tensor_gen.grid_size - 1)
        i1 = np.clip(i1, 0, self.tensor_gen.grid_size - 1)
        j0 = np.clip(j0, 0, self.tensor_gen.grid_size - 1)
        j1 = np.clip(j1, 0, self.tensor_gen.grid_size - 1)
        
        # Weights
        wx = i - i0
        wy = j - j0
        
        # Interpolate eigenvector components
        vx = ((1-wx) * (1-wy) * self.evec_x[j0, i0] +
              wx * (1-wy) * self.evec_x[j0, i1] +
              (1-wx) * wy * self.evec_x[j1, i0] +
              wx * wy * self.evec_x[j1, i1])
        
        vy = ((1-wx) * (1-wy) * self.evec_y[j0, i0] +
              wx * (1-wy) * self.evec_y[j0, i1] +
              (1-wx) * wy * self.evec_y[j1, i0] +
              wx * wy * self.evec_y[j1, i1])
        
        # Normalize
        vec = np.array([vx, vy])
        norm = np.linalg.norm(vec)
        if norm > 1e-6:
            vec /= norm
        
        return vec
    
    def _in_bounds(self, point: np.ndarray) -> bool:
        """Check if point is within grid"""
        x, y = point
        max_coord = self.tensor_gen.grid_size * self.tensor_gen.cell_size
        return (0 <= x < max_coord) and (0 <= y < max_coord)
    
    def _compute_curvature(self, points: List[Tuple]) -> float:
        """Compute curvature from 3 consecutive points"""
        if len(points) < 3:
            return 0
        
        p1, p2, p3 = [np.array(p) for p in points[-3:]]
        
        # Vectors
        v1 = p2 - p1
        v2 = p3 - p2
        
        # Angle between vectors
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1, 1))
        
        # Curvature = angle / distance
        distance = np.linalg.norm(v1) + np.linalg.norm(v2)
        curvature = angle / (distance + 1e-6)
        
        return curvature
    
    def generate_road_network(self, 
                             seed_points: List[Tuple[float, float]],
                             bidirectional: bool = True) -> List[List[Tuple]]:
        """
        Generate full road network from multiple seed points
        
        Args:
            seed_points: Starting points for streamlines
            bidirectional: Trace both forward and backward
        
        Returns:
            List of roads (each road is a list of points)
        """
        roads = []
        
        for seed in seed_points:
            # Forward direction
            road_forward = self.trace_streamline(seed, direction=1)
            
            if bidirectional:
                # Backward direction
                road_backward = self.trace_streamline(seed, direction=-1)
                # Combine (reverse backward part)
                road = road_backward[::-1] + road_forward[1:]
            else:
                road = road_forward
            
            roads.append(road)
        
        return roads
```

#### Friday: Integration & Testing

```python
# tests/integration/test_road_generation.py
"""
Integration test: H-SAGA + Tensor Fields + Road Generation
"""

import pytest
import numpy as np
from src.algorithms.hsaga import Building, BuildingType, Constraint, HSAGA
from src.algorithms.objectives import minimize_cost
from src.spatial.tensor_fields import TensorFieldGenerator
from src.spatial.streamlines import StreamlineIntegrator

def test_end_to_end_campus_planning():
    """Full pipeline test"""
    # 1. Create problem
    buildings = [
        Building("Dorm1", BuildingType.RESIDENTIAL, 3000, 4),
        Building("Dorm2", BuildingType.RESIDENTIAL, 3000, 4),
        Building("Lecture", BuildingType.EDUCATIONAL, 2500, 3),
        Building("Admin", BuildingType.ADMINISTRATIVE, 1500, 2),
        Building("Health", BuildingType.HEALTH, 1000, 2),
    ]
    
    constraints = [
        Constraint("min_distance", {"threshold": 40}),
        Constraint("site_boundary", {"bounds": (0, 0, 500, 500)}),
    ]
    
    objectives = [minimize_cost]  # Simple single-objective for testing
    
    # 2. Optimize building placement
    optimizer = HSAGA(buildings, (0, 0, 500, 500), constraints, objectives)
    optimizer.sa_iterations = 50  # Reduced for testing
    optimizer.ga_generations = 20
    
    result = optimizer.optimize()
    solution = result['solution']
    
    print(f"✅ Optimization completed: {len(solution)} buildings placed")
    
    # 3. Generate tensor field
    tensor_gen = TensorFieldGenerator(grid_size=100, cell_size=5.0)
    tensor_field = tensor_gen.generate(solution)
    
    assert tensor_field.shape == (100, 100, 2, 2)
    print("✅ Tensor field generated")
    
    # 4. Generate road network
    integrator = StreamlineIntegrator(tensor_gen)
    
    # Seed points: center and near each building type
    seed_points = [
        (250, 250),  # Center
        (100, 100),  # Corner
        (400, 400),  # Opposite corner
    ]
    
    roads = integrator.generate_road_network(seed_points, bidirectional=True)
    
    assert len(roads) > 0
    for road in roads:
        assert len(road) > 5  # At least some points
        print(f"  Road with {len(road)} points")
    
    print("✅ Road network generated")
    print(f"🎉 Full pipeline test passed!")

# Run with: pytest tests/integration/ -v -s
```

**Deliverables (Week 2):**
- ✅ Tensor field generator
- ✅ RK4 streamline integrator
- ✅ Road network generation
- ✅ End-to-end integration test
- ✅ Patent-worthy semantic tensor field implementation

---

### **WEEK 3: MULTI-OBJECTIVE OPTIMIZATION**

**Dates:** Nov 18-24  
**Goal:** NSGA-III integration, benchmark comparison  
**Effort:** 40 hours

#### Overview
- Integrate pymoo NSGA-III
- Implement Pareto front analysis
- Benchmark: H-SAGA vs Pure GA vs NSGA-III
- Performance profiling and optimization

#### Monday-Tuesday: NSGA-III Integration

```python
# src/algorithms/nsga3_wrapper.py
"""
NSGA-III multi-objective optimization wrapper
Using pymoo library
"""

from pymoo.algorithms.moo.nsga3 import NSGA3
from pymoo.core.problem import Problem
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.optimize import minimize
from pymoo.util.ref_dirs import get_reference_directions
import numpy as np
from typing import List, Callable
from ..algorithms.hsaga import Building

class CampusPlanningProblem(Problem):
    """
    Pymoo problem wrapper for campus planning
    """
    
    def __init__(self,
                 buildings: List[Building],
                 site_bounds: Tuple,
                 objectives: List[Callable],
                 constraints: List):
        
        self.buildings = buildings
        self.bounds = site_bounds
        self.obj_functions = objectives
        self.const_functions = constraints
        
        n_buildings = len(buildings)
        n_vars = 2 * n_buildings  # (x, y) for each building
        n_obj = len(objectives)
        
        # Define bounds for each variable
        xl = np.array([site_bounds[0], site_bounds[1]] * n_buildings)
        xu = np.array([site_bounds[2], site_bounds[3]] * n_buildings)
        
        super().__init__(
            n_var=n_vars,
            n_obj=n_obj,
            n_constr=len(constraints),
            xl=xl,
            xu=xu
        )
    
    def _evaluate(self, X, out, *args, **kwargs):
        """
        Evaluate population
        X shape: (pop_size, n_vars)
        """
        pop_size = X.shape[0]
        n_obj = len(self.obj_functions)
        n_constr = len(self.const_functions)
        
        F = np.zeros((pop_size, n_obj))  # Objectives
        G = np.zeros((pop_size, n_constr))  # Constraints
        
        for i in range(pop_size):
            # Decode solution
            solution = self._decode_solution(X[i])
            
            # Evaluate objectives
            for j, obj_func in enumerate(self.obj_functions):
                F[i, j] = obj_func(solution)
            
            # Evaluate constraints (< 0 = satisfied)
            for j, const in enumerate(self.const_functions):
                G[i, j] = -1.0 if const.check(solution) else 1.0
        
        out["F"] = F
        out["G"] = G
    
    def _decode_solution(self, x: np.ndarray) -> List[Building]:
        """Convert decision vector to building list"""
        solution = []
        for i, building in enumerate(self.buildings):
            b_copy = Building(
                id=building.id,
                type=building.type,
                area=building.area,
                floors=building.floors,
                position=(x[2*i], x[2*i+1])
            )
            solution.append(b_copy)
        return solution

def optimize_with_nsga3(problem: CampusPlanningProblem,
                       pop_size: int = 100,
                       n_gen: int = 100) -> Dict:
    """
    Run NSGA-III optimization
    """
    # Reference directions for many-objective optimization
    ref_dirs = get_reference_directions(
        "das-dennis",
        problem.n_obj,
        n_partitions=12
    )
    
    # Algorithm setup
    algorithm = NSGA3(
        ref_dirs=ref_dirs,
        pop_size=pop_size,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(eta=20),
        eliminate_duplicates=True
    )
    
    # Run optimization
    res = minimize(
        problem,
        algorithm,
        ('n_gen', n_gen),
        verbose=True
    )
    
    return {
        'pareto_front': res.F,  # Objective values
        'pareto_set': res.X,     # Decision variables
        'n_evals': res.algorithm.evaluator.n_eval,
        'exec_time': res.exec_time
    }
```

#### Wednesday-Thursday: Benchmarking

```python
# benchmarks/algorithm_comparison.py
"""
Benchmark comparison: H-SAGA vs Pure GA vs NSGA-III
"""

import time
import numpy as np
from src.algorithms.hsaga import HSAGA, Building, BuildingType, Constraint
from src.algorithms.nsga3_wrapper import CampusPlanningProblem, optimize_with_nsga3
from src.algorithms.objectives import (
    minimize_cost, 
    minimize_walking_distance,
    maximize_adjacency_satisfaction
)

def create_benchmark_problem(n_buildings: int = 50):
    """Create standardized benchmark problem"""
    np.random.seed(42)  # Reproducibility
    
    building_types = list(BuildingType)
    buildings = []
    
    for i in range(n_buildings):
        b_type = np.random.choice(building_types)
        area = np.random.uniform(1000, 5000)
        floors = np.random.randint(2, 6)
        
        buildings.append(Building(f"B{i}", b_type, area, floors))
    
    constraints = [
        Constraint("min_distance", {"threshold": 30}),
        Constraint("site_boundary", {"bounds": (0, 0, 1000, 1000)}),
    ]
    
    objectives = [
        minimize_cost,
        minimize_walking_distance,
        maximize_adjacency_satisfaction,
    ]
    
    return buildings, constraints, objectives

def benchmark_hsaga(buildings, constraints, objectives, runs=3):
    """Benchmark H-SAGA"""
    results = []
    
    for run in range(runs):
        print(f"H-SAGA run {run+1}/{runs}")
        
        optimizer = HSAGA(buildings, (0, 0, 1000, 1000), constraints, objectives)
        
        start = time.time()
        result = optimizer.optimize()
        runtime = time.time() - start
        
        results.append({
            'fitness': result['fitness'],
            'runtime': runtime,
            'algorithm': 'H-SAGA'
        })
    
    return results

def benchmark_nsga3(buildings, constraints, objectives, runs=3):
    """Benchmark NSGA-III"""
    results = []
    
    for run in range(runs):
        print(f"NSGA-III run {run+1}/{runs}")
        
        problem = CampusPlanningProblem(
            buildings, (0, 0, 1000, 1000), objectives, constraints
        )
        
        start = time.time()
        result = optimize_with_nsga3(problem, pop_size=100, n_gen=100)
        runtime = time.time() - start
        
        # Use hypervolume as fitness metric
        hypervolume = compute_hypervolume(result['pareto_front'])
        
        results.append({
            'hypervolume': hypervolume,
            'runtime': runtime,
            'n_solutions': len(result['pareto_front']),
            'algorithm': 'NSGA-III'
        })
    
    return results

def compute_hypervolume(pareto_front: np.ndarray) -> float:
    """Compute hypervolume indicator"""
    # Simple hypervolume (reference point = [1, 1, 1])
    reference = np.ones(pareto_front.shape[1])
    
    # Sort by first objective
    sorted_front = pareto_front[np.argsort(pareto_front[:, 0])]
    
    volume = 0.0
    for i, point in enumerate(sorted_front):
        if np.all(point < reference):
            # Compute volume contribution
            if i == 0:
                width = point[0]
            else:
                width = point[0] - sorted_front[i-1, 0]
            
            height = reference[1] - point[1]
            depth = reference[2] - point[2]
            volume += width * height * depth
    
    return volume

def run_full_benchmark():
    """Run complete benchmark suite"""
    print("🏁 Starting benchmark suite...")
    print("="*60)
    
    # Create problem
    buildings, constraints, objectives = create_benchmark_problem(n_buildings=50)
    
    # Run benchmarks
    hsaga_results = benchmark_hsaga(buildings, constraints, objectives, runs=3)
    nsga3_results = benchmark_nsga3(buildings, constraints, objectives, runs=3)
    
    # Analyze results
    print("\n📊 RESULTS:")
    print("="*60)
    
    print("\nH-SAGA:")
    for i, r in enumerate(hsaga_results):
        print(f"  Run {i+1}: fitness={r['fitness']:.4f}, time={r['runtime']:.1f}s")
    
    print("\nNSGA-III:")
    for i, r in enumerate(nsga3_results):
        print(f"  Run {i+1}: HV={r['hypervolume']:.4f}, "
              f"n_sol={r['n_solutions']}, time={r['runtime']:.1f}s")
    
    # Summary statistics
    hsaga_avg_time = np.mean([r['runtime'] for r in hsaga_results])
    nsga3_avg_time = np.mean([r['runtime'] for r in nsga3_results])
    
    print("\n📈 SUMMARY:")
    print(f"  H-SAGA avg runtime: {hsaga_avg_time:.1f}s")
    print(f"  NSGA-III avg runtime: {nsga3_avg_time:.1f}s")
    print(f"  Speedup: {nsga3_avg_time / hsaga_avg_time:.2f}x")
    
    return {
        'hsaga': hsaga_results,
        'nsga3': nsga3_results
    }

if __name__ == "__main__":
    results = run_full_benchmark()
```

#### Friday: Performance Profiling

```bash
# Profile H-SAGA
python -m cProfile -o hsaga.prof src/algorithms/hsaga.py
# Analyze with snakeviz
pip install snakeviz
snakeviz hsaga.prof

# Memory profiling
pip install memory_profiler
python -m memory_profiler benchmarks/algorithm_comparison.py
```

**Deliverables (Week 3):**
- ✅ NSGA-III integration
- ✅ Benchmark comparison (H-SAGA vs NSGA-III)
- ✅ Performance profiling report
- ✅ Hypervolume indicator implementation
- ✅ Optimization performance report

---

### **WEEK 4: USER INTERFACE (STREAMLIT)**

**Dates:** Nov 25 - Dec 1  
**Goal:** Interactive web demo with TR/EN support  
**Effort:** 40 hours

#### Overview
- Streamlit app development
- Interactive map (Folium)
- Turkish/English localization (i18n)
- Results visualization (Plotly charts)
- Export functionality

#### Monday-Tuesday: Core UI

```python
# app.py
"""
PlanifyAI - Streamlit Web Interface
Interactive campus planning demo
"""

import streamlit as st
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.graph_objects as go
from src.algorithms.hsaga import Building, BuildingType, Constraint, HSAGA
from src.algorithms.objectives import minimize_cost, minimize_walking_distance
from src.spatial.tensor_fields import TensorFieldGenerator
from src.spatial.streamlines import StreamlineIntegrator
import json

# Page config
st.set_page_config(
    page_title="PlanifyAI - Campus Planning",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Language selection
LANGUAGES = {
    'en': {
        'title': '🏫 PlanifyAI - AI-Powered Campus Planning',
        'subtitle': 'Generative spatial planning with multi-objective optimization',
        'sidebar_header': 'Configuration',
        'site_size': 'Site Size (m)',
        'n_buildings': 'Number of Buildings',
        'optimization_time': 'Optimization Time',
        'quick': 'Quick (~30s)',
        'balanced': 'Balanced (~2min)',
        'thorough': 'Thorough (~5min)',
        'building_types': 'Building Types',
        'residential': 'Residential',
        'educational': 'Educational',
        'administrative': 'Administrative',
        'health': 'Health',
        'social': 'Social & Recreational',
        'run_optimization': '🚀 Run Optimization',
        'results_header': 'Optimization Results',
        'objectives': 'Objectives',
        'cost': 'Total Cost',
        'walking': 'Avg Walking Distance',
        'adjacency': 'Adjacency Score',
        'runtime': 'Runtime',
        'export': 'Export Results'
    },
    'tr': {
        'title': '🏫 PlanifyAI - Yapay Zeka Destekli Kampüs Planlama',
        'subtitle': 'Çok amaçlı optimizasyon ile generatif mekansal planlama',
        'sidebar_header': 'Yapılandırma',
        'site_size': 'Arazi Boyutu (m)',
        'n_buildings': 'Bina Sayısı',
        'optimization_time': 'Optimizasyon Süresi',
        'quick': 'Hızlı (~30sn)',
        'balanced': 'Dengeli (~2dk)',
        'thorough': 'Kapsamlı (~5dk)',
        'building_types': 'Bina Tipleri',
        'residential': 'Yurt/Konut',
        'educational': 'Eğitim',
        'administrative': 'İdari',
        'health': 'Sağlık',
        'social': 'Sosyal ve Rekreasyon',
        'run_optimization': '🚀 Optimizasyonu Başlat',
        'results_header': 'Optimizasyon Sonuçları',
        'objectives': 'Hedefler',
        'cost': 'Toplam Maliyet',
        'walking': 'Ort. Yürüme Mesafesi',
        'adjacency': 'Komşuluk Skoru',
        'runtime': 'Çalışma Süresi',
        'export': 'Sonuçları Dışa Aktar'
    }
}

# Session state initialization
if 'lang' not in st.session_state:
    st.session_state.lang = 'tr'  # Default Turkish
if 'optimized' not in st.session_state:
    st.session_state.optimized = False

def t(key):
    """Get translation"""
    return LANGUAGES[st.session_state.lang].get(key, key)

# Sidebar
with st.sidebar:
    # Language toggle
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🇹🇷 Türkçe", use_container_width=True):
            st.session_state.lang = 'tr'
            st.rerun()
    with col2:
        if st.button("🇬🇧 English", use_container_width=True):
            st.session_state.lang = 'en'
            st.rerun()
    
    st.header(t('sidebar_header'))
    
    # Site parameters
    site_size = st.slider(
        t('site_size'),
        min_value=300,
        max_value=2000,
        value=1000,
        step=100
    )
    
    n_buildings = st.slider(
        t('n_buildings'),
        min_value=10,
        max_value=100,
        value=50,
        step=5
    )
    
    # Optimization preset
    opt_preset = st.radio(
        t('optimization_time'),
        options=['quick', 'balanced', 'thorough'],
        format_func=t
    )
    
    preset_params = {
        'quick': {'sa_iter': 50, 'ga_gen': 20},
        'balanced': {'sa_iter': 100, 'ga_gen': 50},
        'thorough': {'sa_iter': 200, 'ga_gen': 100}
    }
    
    # Building type distribution
    st.subheader(t('building_types'))
    type_dist = {}
    for btype in BuildingType:
        key = btype.value
        type_dist[btype] = st.slider(
            t(key),
            min_value=0,
            max_value=100,
            value=20,
            step=5,
            key=f"dist_{key}"
        ) / 100
    
    # Normalize distribution
    total = sum(type_dist.values())
    if total > 0:
        type_dist = {k: v/total for k, v in type_dist.items()}

# Main content
st.title(t('title'))
st.markdown(f"*{t('subtitle')}*")

# Run optimization button
if st.button(t('run_optimization'), type="primary", use_container_width=True):
    with st.spinner('⏳ Optimizasyon çalışıyor...' if st.session_state.lang == 'tr' 
                    else '⏳ Running optimization...'):
        
        # Generate buildings
        buildings = []
        for i in range(n_buildings):
            # Random type based on distribution
            btype = np.random.choice(
                list(type_dist.keys()),
                p=list(type_dist.values())
            )
            area = np.random.uniform(1000, 5000)
            floors = np.random.randint(2, 6)
            buildings.append(Building(f"B{i}", btype, area, floors))
        
        # Setup optimization
        constraints = [
            Constraint("min_distance", {"threshold": 30}),
            Constraint("site_boundary", {"bounds": (0, 0, site_size, site_size)}),
        ]
        
        objectives = [
            minimize_cost,
            minimize_walking_distance
        ]
        
        # Run H-SAGA
        optimizer = HSAGA(buildings, (0, 0, site_size, site_size), 
                         constraints, objectives)
        optimizer.sa_iterations = preset_params[opt_preset]['sa_iter']
        optimizer.ga_generations = preset_params[opt_preset]['ga_gen']
        
        result = optimizer.optimize()
        
        # Generate roads
        tensor_gen = TensorFieldGenerator(grid_size=100, cell_size=site_size/100)
        tensor_gen.generate(result['solution'])
        integrator = StreamlineIntegrator(tensor_gen)
        
        # Seed points for roads
        seed_points = [
            (site_size/2, site_size/2),
            (site_size/4, site_size/4),
            (3*site_size/4, 3*site_size/4)
        ]
        roads = integrator.generate_road_network(seed_points)
        
        # Store in session state
        st.session_state.result = result
        st.session_state.roads = roads
        st.session_state.buildings = buildings
        st.session_state.site_size = site_size
        st.session_state.optimized = True
    
    st.success('✅ Optimizasyon tamamlandı!' if st.session_state.lang == 'tr'
               else '✅ Optimization complete!')

# Display results
if st.session_state.optimized:
    st.header(t('results_header'))
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cost = minimize_cost(st.session_state.result['solution'])
        st.metric(
            t('cost'),
            f"{cost*100:.1f}M TL",
            delta=None
        )
    
    with col2:
        walking = minimize_walking_distance(st.session_state.result['solution'])
        st.metric(
            t('walking'),
            f"{walking*600:.0f}m",
            delta=None
        )
    
    with col3:
        st.metric(
            "Buildings",
            len(st.session_state.result['solution'])
        )
    
    with col4:
        st.metric(
            t('runtime'),
            f"{st.session_state.result['runtime']:.1f}s"
        )
    
    # Map visualization
    st.subheader("🗺️ Campus Layout")
    
    # Create Folium map
    center = [st.session_state.site_size/2, st.session_state.site_size/2]
    m = folium.Map(
        location=center,
        zoom_start=15,
        tiles='OpenStreetMap'
    )
    
    # Add buildings
    building_colors = {
        BuildingType.RESIDENTIAL: 'blue',
        BuildingType.EDUCATIONAL: 'green',
        BuildingType.ADMINISTRATIVE: 'orange',
        BuildingType.HEALTH: 'red',
        BuildingType.SOCIAL: 'purple'
    }
    
    for building in st.session_state.result['solution']:
        folium.CircleMarker(
            location=[building.position[1], building.position[0]],
            radius=np.sqrt(building.footprint) / 10,
            popup=f"{building.id}: {building.type.value}",
            color=building_colors[building.type],
            fill=True,
            fillOpacity=0.6
        ).add_to(m)
    
    # Add roads
    for road in st.session_state.roads:
        road_coords = [(p[1], p[0]) for p in road]
        folium.PolyLine(
            road_coords,
            color='gray',
            weight=3,
            opacity=0.8
        ).add_to(m)
    
    # Display map
    st_folium(m, width=1200, height=600)
    
    # Convergence plot
    st.subheader("📈 Convergence")
    
    fig = go.Figure()
    
    # SA convergence
    fig.add_trace(go.Scatter(
        y=optimizer.history['sa_fitness'],
        mode='lines',
        name='SA Phase',
        line=dict(color='red', width=2)
    ))
    
    # GA convergence
    fig.add_trace(go.Scatter(
        y=optimizer.history['ga_fitness'],
        mode='lines',
        name='GA Phase',
        line=dict(color='blue', width=2)
    ))
    
    fig.update_layout(
        xaxis_title='Iteration',
        yaxis_title='Fitness',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Export button
    if st.button(t('export'), use_container_width=True):
        # Create export data
        export_data = {
            'buildings': [
                {
                    'id': b.id,
                    'type': b.type.value,
                    'area': b.area,
                    'floors': b.floors,
                    'position': b.position
                }
                for b in st.session_state.result['solution']
            ],
            'roads': [
                [{'x': p[0], 'y': p[1]} for p in road]
                for road in st.session_state.roads
            ],
            'metrics': {
                'cost': float(cost),
                'walking_distance': float(walking),
                'runtime': st.session_state.result['runtime']
            }
        }
        
        # Download JSON
        st.download_button(
            label="📥 Download JSON",
            data=json.dumps(export_data, indent=2),
            file_name="planifyai_result.json",
            mime="application/json"
        )
```

**Deliverables (Week 4):**
- ✅ Streamlit web app
- ✅ TR/EN localization
- ✅ Interactive map (Folium)
- ✅ Convergence visualization (Plotly)
- ✅ Export functionality (JSON)
- ✅ Responsive UI for demo

---

### **WEEK 5: INTEGRATION & TESTING**

**Dates:** Dec 2-8  
**Goal:** End-to-end testing, bug fixes, performance tuning  
**Effort:** 40 hours

#### Focus Areas
1. Integration testing (all modules together)
2. Edge case handling
3. Performance optimization (M1-specific)
4. Code cleanup and refactoring
5. Documentation updates

#### Key Tasks
- Write integration test suite (pytest)
- Fix discovered bugs
- Profile and optimize hot spots
- Memory leak detection
- Code coverage >85%
- Refactor for maintainability

**Tools:** Cursor (refactoring), ChatGPT Pro (debugging), pytest, cProfile

**Deliverables:**
- ✅ Stable MVP (no critical bugs)
- ✅ Test coverage >85%
- ✅ Performance report (M1 benchmarks)
- ✅ Refactored codebase (clean, maintainable)

---

### **WEEK 6: DOCUMENTATION (CODE)**

**Dates:** Dec 9-15  
**Goal:** Complete code documentation  
**Effort:** 35 hours

#### Deliverables
1. **README.md** (TR/EN)
   - Project overview
   - Installation guide
   - Quick start tutorial
   - Architecture overview
   - Contributing guidelines

2. **API Documentation** (EN)
   - Module documentation (mkdocs)
   - Function docstrings
   - Type hints
   - Usage examples

3. **User Guide** (TR)
   - Interface walkthrough
   - Parameter explanations
   - Best practices
   - Troubleshooting

4. **Developer Guide** (EN)
   - Architecture deep dive
   - Algorithm explanations
   - Extension points
   - Testing guide

**Tools:** Claude (documentation generation), mkdocs, Cursor (docstrings)

---

### **WEEK 7: THESIS WRITING**

**Dates:** Dec 16-22  
**Goal:** Complete thesis draft (80%+)  
**Effort:** 45 hours (critical week)

#### Thesis Structure (60-80 pages, Turkish)

**Chapter 1: Giriş (10 pages)**
- Problem tanımı
- Motivasyon
- Araştırma soruları
- Katkılar
- Tez organizasyonu

**Chapter 2: Literatür Taraması (15 pages)**
- Mekansal planlama geçmişi
- Optimizasyon algoritmaları (GA, SA, NSGA-III)
- Tensor field methods
- İlgili çalışmalar
- Araştırma boşlukları

**Chapter 3: Yöntem (20 pages)**
- Problem formülasyonu
- H-SAGA algoritması (detaylı)
- Tensor field road generation
- Amaç fonksiyonları
- Kısıtlar
- Uygulama detayları

**Chapter 4: Uygulama (10 pages)**
- Sistem mimarisi
- Teknoloji stack
- M1 optimizasyonları
- Kullanıcı arayüzü

**Chapter 5: Deneysel Sonuçlar (10 pages)**
- Benchmark karşılaştırmaları
- Performans metrikleri
- Örnek olay çalışmaları
- Görselleştirmeler

**Chapter 6: Sonuç ve Gelecek Çalışmalar (5 pages)**
- Özet ve katkılar
- Kısıtlamalar
- Gelecek çalışma önerileri

**Tools:** ChatGPT Pro (Turkish writing), Gemini (figures), Claude (review)

**Writing Strategy:**
- Days 1-2: Chapters 1-2 (introduction, literature)
- Days 3-4: Chapter 3 (methodology)
- Day 5: Chapter 4 (implementation)
- Day 6: Chapter 5 (results)
- Day 7: Chapter 6 + revisions

---

### **WEEK 8: FINALIZATION & DEFENSE**

**Dates:** Dec 23-30  
**Goal:** Final submission package  
**Effort:** 35 hours

#### Deliverables

**1. Thesis Finalization (2 days)**
- Incorporate supervisor feedback
- Proofread (Turkish)
- Format (university template)
- Generate table of contents, figures, references
- PDF export

**2. Defense Presentation (2 days)**
- 20-30 slides (Turkish)
- Problem & motivation (5 slides)
- Approach & innovation (8 slides)
- Implementation & demo (5 slides)
- Results (5 slides)
- Q&A preparation (2 slides)

**3. Demo Video (1 day)**
- 5-10 minute video (Turkish)
- Screen recording (Streamlit app)
- Voiceover explanation
- Edit and polish

**4. GitHub Repository (1 day)**
- Final code cleanup
- Complete README (TR/EN)
- Add LICENSE (MIT)
- Tag v1.0.0 release
- Ensure repo is public

**5. Submission Package (1 day)**
- Thesis PDF
- Presentation PDF
- Demo video link
- GitHub repo link
- All deliverables zipped

**Tools:** ChatGPT (slides), Claude (proofreading), Keynote/PowerPoint, ScreenFlow/OBS

---

## 🛠️ PART 5: GIT WORKFLOW & VERSION CONTROL

### Branch Strategy (GitHub Flow - Simplified)

```
main (production)
  └── develop (active development)
        ├── feature/hsaga-implementation
        ├── feature/tensor-fields
        ├── feature/nsga3-integration
        ├── feature/streamlit-ui
        └── bugfix/constraint-violation
```

**Rules:**
1. `main` branch: Always deployable (tagged releases only)
2. `develop` branch: Integration branch (merge features here)
3. `feature/*` branches: New features (1 week max lifetime)
4. `bugfix/*` branches: Bug fixes (short-lived)
5. No direct commits to `main` or `develop`

### Commit Message Standard (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Build/tool changes

**Examples:**
```bash
git commit -m "feat(hsaga): implement SA→GA hybrid algorithm

- SA global exploration (200 iterations)
- GA local refinement (100 generations)
- Elite preservation + diversity injection

Based on Li et al. (2025)"

git commit -m "fix(constraints): handle edge case in min_distance check

Building positions at exactly threshold distance
were incorrectly rejected. Added epsilon tolerance.

Fixes #12"

git commit -m "docs: add Turkish README translation"

git commit -m "test(objectives): add unit tests for cost function

- Test normalization
- Test edge cases (zero buildings)
- Test type-specific costs"
```

### Pull Request Workflow

**Step 1: Create Feature Branch**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/my-feature
```

**Step 2: Develop and Commit**
```bash
# Make changes
git add .
git commit -m "feat: implement feature"
# Repeat...
```

**Step 3: Push and Create PR**
```bash
git push -u origin feature/my-feature
# Create PR on GitHub: feature/my-feature → develop
```

**Step 4: Code Review (Self-review for solo project)**
- Check: Tests pass?
- Check: Documentation updated?
- Check: No merge conflicts?

**Step 5: Merge**
```bash
# Squash merge to develop
git checkout develop
git merge --squash feature/my-feature
git commit -m "feat: my feature

[detailed description]"
git push origin develop

# Delete feature branch
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

### Release Tagging

```bash
# When ready for submission
git checkout main
git merge develop
git tag -a v1.0.0 -m "PlanifyAI MVP Release

- H-SAGA optimization
- Tensor field road generation
- Streamlit web UI (TR/EN)
- Benchmark results
- Complete documentation

Academic submission version"

git push origin main --tags
```

### GitHub Actions CI/CD (Optional but Recommended)

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest  # M1 runner if available
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## 📄 PART 6: DOCUMENTATION STRATEGY (TR/EN)

### Documentation Structure

```
docs/
├── README.md (EN)
├── README.tr.md (TR)
├── CONTRIBUTING.md (EN)
├── api/
│   ├── algorithms.md
│   ├── spatial.md
│   └── objectives.md
├── user-guide/
│   ├── installation.tr.md
│   ├── quickstart.tr.md
│   ├── parameters.tr.md
│   └── troubleshooting.tr.md
├── developer-guide/
│   ├── architecture.md
│   ├── algorithms.md
│   ├── extending.md
│   └── testing.md
└── thesis/
    ├── chapters/
    ├── figures/
    └── references.bib
```

### Documentation Generation with AI Tools

#### **README.md (Claude)**

**Prompt:**
```
Generate a comprehensive README.md for PlanifyAI project.

Context:
- AI-powered campus planning tool
- Python 3.11, M1-optimized
- H-SAGA + tensor fields
- Streamlit UI (TR/EN)
- MIT License

Sections:
1. Project overview (2 paragraphs)
2. Features (bullet list)
3. Installation (step-by-step)
4. Quick start (code example)
5. Architecture (brief overview)
6. Contributing
7. License
8. Citation

Tone: Professional but friendly
```

#### **API Documentation (Cursor + mkdocs)**

```python
# Example docstring format (use Cursor to generate)

def minimize_cost(solution: List[Building]) -> float:
    """
    Calculate total construction cost objective.
    
    This objective function computes the total construction cost
    based on building area and type-specific cost rates. The result
    is normalized to [0, 1] range for fair weighting with other objectives.
    
    Args:
        solution: List of Building objects with assigned positions
        
    Returns:
        Normalized cost value in [0, 1] where lower is better
        
    Example:
        >>> buildings = [Building("B1", BuildingType.RESIDENTIAL, 3000, 2)]
        >>> cost = minimize_cost(buildings)
        >>> print(f"Cost: {cost:.4f}")
        Cost: 0.0450
        
    Note:
        Cost rates are based on 2025 Turkish construction market data:
        - Residential: 1,500 TL/m²
        - Educational: 2,000 TL/m²
        - Administrative: 1,800 TL/m²
        - Health: 2,500 TL/m²
        - Social: 1,600 TL/m²
        
    See Also:
        - :func:`minimize_walking_distance`: Accessibility objective
        - :func:`maximize_adjacency_satisfaction`: Spatial relationships
    """
    # Implementation...
```

#### **User Guide (ChatGPT Pro - Turkish)**

**Prompt:**
```
Türkçe kullanıcı kılavuzu yaz: PlanifyAI kurulum ve kullanım

Bölümler:
1. Kurulum (macOS M1 için)
2. İlk kullanım (adım adım)
3. Parametre açıklamaları
4. Sonuçları yorumlama
5. Sık sorulan sorular
6. Sorun giderme

Hedef kitle: Şehir plancısı, mimar (teknik olmayan)
Ton: Açıklayıcı, dostane
```

#### **Thesis Chapters (ChatGPT Pro + Gemini)**

**Week 7 strategy:**

**Day 1-2: ChatGPT Pro for Chapter drafts (Turkish)**
```
Prompt sequence:
1. "Bölüm 1 yaz: Giriş ve Problem Tanımı"
2. "Bölüm 2 yaz: Literatür Taraması - Mekansal Optimizasyon"
3. [Continue...]
```

**Day 3-4: ChatGPT Pro for Methodology**
```
"Bölüm 3 yaz: Yöntem
- H-SAGA algoritması (Li et al. 2025 based)
- Matematiksel formülasyon
- Tensor field yol ağı üretimi
- Amaç fonksiyonları"
```

**Day 5: Gemini for Figures**
```
"Generate architecture diagram from this description:
[paste system architecture]
Output: Mermaid diagram code"
```

**Day 6-7: Claude for Review**
```
"Review this thesis chapter (Turkish):
[paste chapter]

Check:
1. Academic tone
2. Clarity
3. Logical flow
4. Grammar
5. Citations

Suggest improvements."
```

### Bilingual Documentation Workflow

**English First Approach:**
1. Write technical docs in English (API, developer guide)
2. Use Claude/ChatGPT to translate to Turkish
3. Review and adapt for Turkish audience

**Turkish First for User-Facing:**
1. Write user guide in Turkish (target audience)
2. Translate to English for GitHub visibility
3. Maintain both versions side-by-side

**Example:**
```
docs/
├── README.md (EN)
├── README.tr.md (TR - link at top of EN version)
└── user-guide/
    ├── quickstart.md (EN)
    └── quickstart.tr.md (TR)
```

---

## 🎯 PART 7: SUCCESS METRICS & RISK MITIGATION

### Success Criteria (Checklist)

**Week-by-Week Milestones:**

- [ ] Week 1: H-SAGA working + 80% test coverage
- [ ] Week 2: Tensor fields + road generation integrated
- [ ] Week 3: NSGA-III + benchmark results
- [ ] Week 4: Streamlit app deployed (local)
- [ ] Week 5: All tests passing, no critical bugs
- [ ] Week 6: Documentation complete (code)
- [ ] Week 7: Thesis draft 80%+ complete
- [ ] Week 8: Final submission package ready

**MVP Acceptance Criteria:**

- [ ] Can optimize 50 buildings in <2 minutes
- [ ] Generates road network automatically
- [ ] 3 objectives: cost, accessibility, adjacency
- [ ] Web UI works (TR/EN)
- [ ] Visual output (2D map)
- [ ] Export results (JSON)
- [ ] Documentation (README, user guide, thesis)
- [ ] Source code on GitHub (MIT license)
- [ ] Demo video (5 minutes)

### Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Algorithm doesn't converge** | Medium | High | Start with simple 10-building test, incrementally scale up |
| **M1 performance issues** | Low | Medium | Profile early (Week 1), optimize hot spots, use NumPy Accelerate |
| **Streamlit crashes/slow** | Medium | Medium | Keep UI simple, use caching (@st.cache_data), test with small datasets |
| **Thesis writing time overrun** | High | High | Start outline in Week 4, use AI tools heavily (ChatGPT Pro), allocate full Week 7 |
| **Scope creep** | High | High | STRICT MVP scope, defer everything else to "Future Work", no feature additions after Week 4 |
| **Bug discovery in Week 8** | Medium | High | Extensive testing in Week 5, feature freeze after Week 6 |
| **Supervisor feedback loop** | Low | Medium | Early draft review (Week 7 midpoint), incorporate feedback in Week 8 |
| **Mac hardware failure** | Very Low | Critical | Daily git push, GitHub backup, iCloud backup for documents |

### Contingency Plans

**If Running Behind Schedule (Week 4 checkpoint):**

**Option A: Reduce scope (preferred)**
- Remove NSGA-III comparison (keep only H-SAGA)
- Simplify UI (remove some visualizations)
- Reduce test coverage target to 70%

**Option B: Extend hours**
- Add weekend work (6-8 hours Sat/Sun)
- Reduce sleep (not recommended but possible short-term)

**Option C: Defer non-critical**
- Skip GPU profiling
- Minimal API documentation (focus on user guide)
- Shorter thesis chapters (60 pages instead of 80)

**If Ahead of Schedule (Week 6 checkpoint):**

**Bonus Features (prioritize top-down):**
1. ✅ Import real campus data (OSM)
2. ✅ 3D visualization (Three.js basic)
3. ✅ NSGA-III Pareto front visualization
4. ✅ Additional objectives (green space, sunlight)
5. ✅ Constraint violation visualization

**Use Extra Time For:**
- More thesis polishing
- Better UI/UX
- More comprehensive testing
- Academic paper draft (future publication)

---

## 📝 FINAL SUMMARY

### Project Snapshot

**Type:** University graduation project (Computer Science/Engineering)  
**Duration:** 8 weeks (Nov 4 - Dec 30, 2025)  
**Deliverable:** MVP web application + academic thesis  
**Platform:** Apple M1 MacBook Air  
**Language:** Python 3.11 (backend), Streamlit (frontend)

### Technology Stack (Confirmed)

**Backend:**
- Python 3.11, NumPy (Accelerate), SciPy, pandas
- pymoo (NSGA-III), GeoPandas, Shapely, OSMnx
- Custom: H-SAGA, Tensor fields, RK4 integration

**Frontend:**
- Streamlit (web UI)
- Folium (maps)
- Plotly (charts)

**Dev Tools:**
- Cursor IDE (AI coding)
- GitHub (version control)
- pytest (testing)
- mkdocs (documentation)

**AI Tools:**
- Cursor: Code generation (80% of coding time)
- ChatGPT Pro: Research, debugging, thesis writing (TR)
- Claude: Architecture, documentation, review
- Gemini: Figures, diagrams, supplementary research

### Key Innovations

1. **H-SAGA Algorithm:** Reverse hybrid (SA→GA), patent-worthy
2. **Semantic Tensor Fields:** Building type-aware road generation
3. **Turkish Context:** Local data, standards, bilingual UI
4. **M1 Optimization:** Apple Accelerate, vectorization, threading
5. **Rapid Development:** 8 weeks from research to MVP

### Expected Outcomes

**Academic:**
- ✅ High-quality thesis (60-80 pages)
- ✅ Strong defense presentation
- ✅ Potential conference paper submission
- ✅ Grade: AA/A (target)

**Technical:**
- ✅ Working MVP (production-quality for demo)
- ✅ GitHub repository (300+ stars potential)
- ✅ Documentation (developer + user friendly)
- ✅ Benchmark results (publishable)

**Career:**
- ✅ Portfolio project (impressive for job applications)
- ✅ Open-source contribution
- ✅ Research experience
- ✅ AI/optimization expertise demonstration

---

## 🎉 CONCLUSION

Bu 8 haftalık plan:

✅ **Realistic:** Tek kişi, 8 saat/gün, achievable scope  
✅ **Detailed:** Haftalık breakdown, günlük tasks, kod örnekleri  
✅ **M1-Optimized:** Platform-specific best practices  
✅ **AI-Powered:** Strategic tool usage for maximum efficiency  
✅ **Academic-Ready:** Thesis + defense aligned with plan  
✅ **Bilingual:** TR/EN documentation strategy  
✅ **Risk-Aware:** Contingency plans, clear success criteria

**Başarı Şansı:** 90%+ (with discipline and focus)

**Next Step:** Start Monday, November 4, 2025 - Week 1, Day 1

**Motivation:** "The best way to predict the future is to build it." - Alan Kay

**Ready? LET'S BUILD PLANIFYAI!** 🚀🏫🎓

---

*Sorular, değişiklikler, veya detaylandırma gerekirse hemen sorun!*
