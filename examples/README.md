# PlanifyAI Examples

This directory contains complete examples demonstrating how to use the PlanifyAI multi-objective optimization system.

## 📚 Available Examples

### 1. Complete NSGA-III Workflow (`nsga3_complete_workflow.py`)

End-to-end example showing:
- Building configuration
- NSGA-III optimization with different objective profiles
- Result analysis and statistics
- Visualization generation
- Profile comparison

**Usage:**
```bash
python examples/nsga3_complete_workflow.py
```

**Output:**
- Console output with statistics and analysis
- Visualization plots in `examples/output/`:
  - `parallel_coordinates.png` - Multi-dimensional view
  - `objective_matrix.png` - Pairwise trade-offs
  - `pareto_2d.png` - 2D Pareto front
  - `pareto_3d.png` - 3D Pareto front

### 2. REST API Usage (`api_usage_examples.py`)

Examples of using the REST API for:
- Listing objective profiles
- Running NSGA-III optimization
- Generating visualizations
- Computing statistics

**Prerequisites:**
1. Start the API server:
   ```bash
   cd backend
   uvicorn api.main:app --reload
   ```

2. Install requests:
   ```bash
   pip install requests
   ```

**Usage:**
```bash
python examples/api_usage_examples.py
```

**Output:**
- Visualization plots in `examples/api_output/`
- Statistics and best solution printed to console

## 🎯 Objective Profiles

The system includes 4 predefined objective profiles:

### 1. **Standard** (Default)
- Basic multi-objective optimization
- Objectives: Cost, Walking Distance, Adjacency
- Equal weights (0.33 each)
- Best for: Quick tests and basic planning

### 2. **Research-Enhanced** (Recommended)
- All research-based enhanced objectives
- Objectives: Cost, Walking Distance (2SFCA), Adjacency, Diversity (Shannon Entropy)
- Balanced weights (0.25 each)
- Best for: High-quality campus planning with scientific rigor

### 3. **15-Minute City**
- Accessibility-focused planning
- Heavy emphasis on walking accessibility (0.5 weight)
- Best for: Urban planning with walkability priority

### 4. **Campus Planning**
- Adjacency-focused for educational facilities
- Emphasizes building relationships (0.5 weight)
- Best for: Campus layout optimization

### Custom Profiles

You can create custom profiles with your own weights:

```python
from src.algorithms import create_custom_profile

custom = create_custom_profile(
    name="My Custom Profile",
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

## 📊 Visualization Types

### 1. Parallel Coordinates
- Shows all objectives simultaneously
- Best for: Understanding multi-dimensional trade-offs
- Works with: Any number of objectives (2+)

### 2. Objective Matrix
- Pairwise scatter plots and histograms
- Best for: Detailed trade-off analysis
- Shows: Correlations between objectives

### 3. 2D Pareto Front
- Classic 2-objective scatter plot
- Best for: Clear visualization of trade-offs
- Requires: Exactly 2 objectives

### 4. 3D Pareto Front
- Interactive 3D scatter plot
- Best for: Three-objective problems
- Requires: Exactly 3 objectives

## 🔧 Configuration Examples

### Small Problem (Quick Testing)
```python
config = NSGA3RunnerConfig(
    population_size=30,
    n_generations=30,
    objective_profile=ProfileType.STANDARD,
    seed=42
)
```

### Medium Problem (Balanced)
```python
config = NSGA3RunnerConfig(
    population_size=50,
    n_generations=50,
    objective_profile=ProfileType.RESEARCH_ENHANCED,
    seed=42
)
```

### Large Problem (High Quality)
```python
config = NSGA3RunnerConfig(
    population_size=100,
    n_generations=100,
    n_partitions=12,
    use_two_layer=True,
    n_partitions_inner=3,
    objective_profile=ProfileType.RESEARCH_ENHANCED,
    seed=42
)
```

## 📈 Performance Tips

1. **Start Small**: Begin with small population (30) and generations (30)
2. **Profile Choice**: Use `STANDARD` for testing, `RESEARCH_ENHANCED` for production
3. **Seed**: Set a seed for reproducible results
4. **Visualization**: Generate visualizations after optimization, not during
5. **API**: Use REST API for web applications, direct Python for scripts

## 🚀 Quick Start

1. **Install Dependencies:**
   ```bash
   pip install numpy matplotlib
   ```

2. **Run Complete Workflow:**
   ```bash
   python examples/nsga3_complete_workflow.py
   ```

3. **Check Output:**
   ```bash
   ls examples/output/
   ```

4. **Try REST API:**
   ```bash
   # Terminal 1: Start API
   cd backend && uvicorn api.main:app --reload

   # Terminal 2: Run example
   python examples/api_usage_examples.py
   ```

## 📖 API Documentation

When the API server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎓 Learning Path

1. **Beginner**: Start with `nsga3_complete_workflow.py` to understand the basics
2. **Intermediate**: Experiment with different profiles and configurations
3. **Advanced**: Use `api_usage_examples.py` for web integration
4. **Expert**: Create custom profiles and objectives

## 🤝 Support

For issues or questions:
- Check the main README: `../README.md`
- API Documentation: http://localhost:8000/docs
- Development Roadmap: `../DEVELOPMENT_ROADMAP.md`

## 📝 License

See main project LICENSE file.
