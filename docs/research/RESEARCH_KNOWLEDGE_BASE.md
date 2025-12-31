# PlanifyAI Master Research Knowledge Base

> **Status:** Active / In-Progress
> **Last Updated:** 2025-12-10
> **Source Directory:** `docs/research/`

This document serves as the single source of truth for all theoretical frameworks, algorithms, mathematical models, and implementation guidelines extracted from the project's research repository. It is organized by **Core Intelligence Pillars**.

---

## ⚡️ Pillar 1: Urban Optimization & Metrics
*Focus: 15-Minute City, Accessibility, and Spatial Equity*

### 1.1 The 15-Minute City Concept (Turkish Context)
**Source:** `15-Minute City Optimization Analysis.docx`

**Core Definition:** An urban planning model where daily needs (living, work, commerce, healthcare, education, entertainment) are accessible within a 15-minute walk or bike ride.

**The "Turkey Adaptation":**
- **Cultural Anchors:** The model explicitly emphasizes local cultural elements missing from Western models:
    - **Mosques (Camii):** Central node for community interaction.
    - **Semt Pazars (Weekly Markets):** Critical for food security and social cohesion, requiring temporal spatial planning (streets becoming markets).
    - **Tea Gardens (Çay Bahçesi):** Essential public gathering spaces.
- **Aging Population:** Turkey's rapidly aging demographic requires steeper accessibility decay curves for elderly mobility models.

### 1.2 Mathematical Metrics & Formulations
#### A. Walking Distance & Isochrones
- **Pedestrian Graph:** Distance is measured via network topology, not Euclidean distance.
- **Slope Penalty:** Walking speed $v$ is adjusted for terrain slope $s$:
  $$v_{adj} = v_{flat} \cdot e^{-k \cdot |s|}$$
  *Typical Tobler's Hiking Function adaptation for urban environments.*

#### B. Accessibility Metrics
1.  **Gravity Models:** Interaction potential decays with distance.
    $$A_i = \sum_{j} O_j \cdot f(d_{ij})$$
    where $A_i$ is accessibility at origin $i$, $O_j$ is opportunity at destination $j$, and $f(d_{ij})$ is the impedance function (typically exponential or power law).
2.  **2-Step Floating Catchment Area (2SFCA):**
    - **Step 1:** Calculate supply-to-demand ratio $R_j$ for each facility $j$ within catchment $d_0$.
    - **Step 2:** Sum ratios $R_j$ for all facilities accessible to population $i$.
    - *Critical for healthcare and education to prevent capacity overcrowding.*

#### C. Fitness Function Vector
The optimization requires a multi-objective vector, not a single scalar:
$$F(x) = [Coverage, Diversity, Equity, Cost]$$
- **Entropy (Diversity):** Shannon Entropy used to measure mixed-use balance.
  $$H = -\sum p_i \ln(p_i)$$

---

## 🧬 Pillar 2: Generative Design & Geometry
*Focus: 3D Form, Tensor Fields, and Road Networks*

### 2.1 Tensor Fields for Urban Layout
**Sources:** `3D Urban Design Optimization Analysis.docx`, `Adaptive RK4 Streamline Generation Analysis.docx`

**Concept:** Representing "urban flow" and alignment as a continuous mathematical field rather than discrete objects.
- **Tensor Representation:** A symmetric 2x2 (or 3x3 for 3D) tensor field $T(\mathbf{x})$ defines preferred directions at every point.
- **Eigen-Decomposition:**
  - **Major Eigenvector ($e_1$):** Defines the primary direction (e.g., main roads, skyscraper structural grain).
  - **Minor Eigenvector ($e_2$):** Defines the secondary direction (e.g., side streets, floor plates).
  - **Eigenvalues ($\lambda_1, \lambda_2$):** Define the "strength" or anisotropy of the alignment.

### 2.2 Adaptive Runge-Kutta (RK45) for Streamlines
**Source:** `Adaptive RK4 Streamline Generation Analysis.docx`

**The Problem:** Fixed-step integration (RK4) fails in urban road generation because city curvature is heterogeneous. It wastes compute in straight sections and "crashes" (overshoots) in complex intersections.

**The Solution:** **Dormand-Prince 5(4) Method with Adaptive Step Size.**
- **Local Extrapolation:** Computes both 4th and 5th order solutions to estimate error $E$.
- **Step Size Control:**
  $$h_{new} = h_{old} \cdot S \cdot \left(\frac{Tol}{E}\right)^{1/5}$$
  *(S is safety factor ~0.9)*

**Implementation Criticals (Python `scipy.integrate.RK45`):**
1.  **Do NOT use `solve_ivp`:** It lacks custom stopping criteria.
2.  **Manual Stepping Loop:** Use `while solver.status == 'running': solver.step()` algorithm.
3.  **Stopping Criteria:**
    - **Boundary:** Particle leaves simulation box.
    - **Singularity:** Velocity magnitude $|\mathbf{v}| < \epsilon$ (indicates a node/intersection).
    - **Proximity:** KD-Tree check against existing paths (prevent overlap).

### 2.3 Field Singularity Detection & Topology
**Source:** `Tensor Field Singularity Detection Analysis.docx`

**Core Concept:** Detecting "Structural Decision Points" where direction is ambiguous ($\lambda_1 = \lambda_2$).
- **Stable Singularities (Half-Integer):**
    - **Wedge ($+1/2$):** Origin or terminus of a street/flow.
    - **Trisector ($-1/2$):** Bifurcation or "Y" intersection.
- **Detection Algorithm:**
    - Solve roots of $D_1 = T_{xy} = 0$ and $D_2 = T_{xx} - T_{yy} = 0$.
    - **Poincaré Index:** Integrate angle change around cell boundary (robust to $\pi$-symmetry).

### 2.4 Implementation Guide: Tensor Field Road Networks
**Source:** `Tensor Field Road Generation Guide.docx`

**Practical Stack (Python):**
*   **Core:** `scipy.integrate.RK45` (Streamlines), `scipy.interpolate.RegularGridInterpolator` (Tensor Field sampling).
*   **Hardware:** **CPU-Only**. GPU (CuPy) provides no benefit for sequential streamline tracing of small vectors (20MB data).
*   **Hybrid Strategy:**
    *   **Major Roads:** Trace via Tensor Field (RK45). Creates the "Skeleton".
    *   **Minor Roads:** Recursive Block Subdivision (Parish & Müller rules) inside the skeleton cells. Avoids complex minor-eigenvector singularities.

---

## 🧠 Pillar 3: Adaptive Planning & Intelligence
*Focus: Post-Occupancy Evaluation (POE) and Reinforcement Learning (RL)*

### 3.1 The "Sentient" Environment Loop
**Source:** `Adaptive Planning Through Post-Occupancy Evaluation.docx`

**Workflow:**
1.  **Generate:** AI proposes design.
2.  **Build/Simulate:** Design is realized (or deeply simulated).
3.  **Sense:** Gather "As-Lived" data.
    - **Passive:** BMS (Energy), IoT (Air Quality, Noise), Wi-Fi (Occupancy/Movement).
    - **Active:** Surveys (Sentiment, Comfort).
4.  **Learn:** RL update mechanism.

### 3.2 Machine Learning Pipeline
- **Sentiment Analysis:** VADER or BERT for processing unstructured tenant complaints/feedback.
- **Clustering:** K-Means to identify "User Archetypes" (e.g., *Thermal Sensitive*, *Acoustic Sensitive*).

### 3.3 The RL Reward Function
A composite reward function derived from POE data to train the generative agent:
$$R = w_{sat} \cdot S_{norm} + w_{energy} \cdot (1 - E_{norm}) + w_{maint} \cdot (1 - M_{norm}) - P_{constraint}$$
- $S_{norm}$: Normalized Satisfaction Score (from users).
- $E_{norm}$: Normalized Energy Intensity (EUI).
- $M_{norm}$: Normalized Maintenance Tickets.
- $P_{constraint}$: Penalty for breaking code/physics.

---

## 📜 Pillar 4: Regulatory & Compliance Engine
*Focus: Turkish Building Codes and Automated Checking*

### 4.1 The Federated Regulation Stack
**Source:** `Automated Building Code Compliance Analysis.docx`

An automated checker must handle the hierarchy of Turkish Law:
1.  **National General:** *Planlı Alanlar İmar Yönetmeliği (PAİY)* - (Core setbacks, rules).
2.  **National Specific:** *Türkiye Bina Deprem Yönetmeliği (TBDY 2018)* - (Seismic gaps, structural).
3.  **Standards:** *TSE (TS 9111, TS 12576)* - (Accessibility, ramps $> 90cm$).
4.  **Local/Parcel:** *Plan Notları* & *Uygulama İmar Planı* - (KAKS/FAR, TAKS/Footprint).

### 4.2 Handling "The Compliance Gap"
- **Problem:** Regulations exist but enforcement fails (key cause of earthquake damage).
- **Solution:** Transparency.
    - **Blockchain:** Immutable audit trail of compliance checks per permit.
    - **Hybrid Engine:**
        - **IfcOpenShell:** For parsing BIM (IFC) geometry.
        - **pySHACL:** For validating prescriptive rules against ifcOWL graphs.
        - **PostGIS:** For validating district rules (setbacks against parcel lines).

### 4.3 Technical Implementation: RASE Methodology
Use **RASE** (Requirements, Applicability, Selection, Exception) to parse text laws into JSON rules.
- **Example JSON Rule (Seismic):**
```json
{
  "ruleId": "TBDY-SecX",
  "type": "performance",
  "applicability": ["Region.SeismicZone == 1", "Building.Height > 10m"],
  "constraint": {
    "function": "calculate_seismic_gap_srss",
    "operator": "gte",
    "value": 0
  },
  "violationMetric": "required_gap - actual_gap"
}
```

---

## 🏗 Pillar 5: Digital Twin & BIM Intelligence
*Focus: Data Pipelines, Energy Modeling, and Simulation*

### 5.1 The Hybrid BIM Architecture
**Source:** `BIM Integration for AI Planning.docx`

A single tool cannot handle both high-fidelity authoring and scalable optimization. A hybrid architecture is required:
1.  **High-Fidelity Authoring (The "Write" Layer):**
    -   **Tool:** Autodesk Revit API.
    -   **Role:** Creating parametric families, managing detailed views, and executing final design changes (Transactions).
    -   **Advantage:** Deep integration, parametric integrity.
2.  **Scalable Computation (The "Read/Compute" Layer):**
    -   **Tool:** IfcOpenShell (C++/Python).
    -   **Role:** Parsing massive IFC datasets on servers, geometry extraction, and running headless optimization loops.
    -   **Advantage:** Vendor-agnostic, high-performance, open standards.

### 5.2 Building Energy Modeling (BEM)
**Source:** `Building Energy Modeling Integration for Sustainable Spatial Planning.docx`

**Core Stack:**
-   **Engine:** **EnergyPlus** (Physics engine for heat balance, loads, HVAC).
-   **Interface:** **OpenStudio** (SDK for manipulating EnergyPlus models programmatically).
-   **Parametric:** **Ladybug Tools** (Rhino/Grasshopper/Python integration).

**Optimization Workflow:**
1.  **Parametric Sweep:** Use `eppy` or `honeybee-energy` to programmatically modify IDF/OSM files (e.g., rotate building 5° increments).
2.  **Surrogate Modeling:** Full BEM is too slow for 1000s of iterations. Train an ML surrogate (Neural Net) on ~200 high-fidelity EnergyPlus runs to predict EUI for the rest of the search space.

### 5.3 Traffic Simulation & Validation
**Source:** `Traffic Microsimulation for Spatial Planning.docx`

- **Stack:**
    - **Strategic (MATSim):** Regional activity-based demand modeling (Who goes where?).
    - **Tactical (SUMO):** Micro-simulation of intersections and delays (Does it jam?).
- **Generative Loop (SITL):** Simulation-in-the-Loop.
    - Use SUMO output (Delay, $CO_2$) as the **Fitness Function**.
    - **Constraint:** "Minimal Viable Capability" - Road network must handle peak load without gridlock.

### 5.4 Transfer Learning for Spatial Optimization
**Source:** `Transfer Learning in Spatial Planning.docx`

- **Problem:** "Curse of Uniqueness" in new projects (Data Scarcity).
- **Solution:** Transfer knowledge from Source (e.g., Campus) to Target (e.g., Industrial Park).
- **Technique:** **Adversarial Domain Adaptation (DANN)**.
    - Align feature distributions (e.g., building density, network centrality) so the optimizer "understands" the new terrain instantly.

---

## 🎓 Pillar 6: Campus Systems & Network Logic
*Focus: Topological Optimization, Road Hierarchy, and Universal Access*

### 6. Campus Road Network Design (Turkish Context & Graph Theory) [Batch 2]
**Source:** *Campus_Road_Network_Design.docx*

**Core Concept:**
Transitioning from general graph theory to specific Turkish university campus typologies. The focus is on a hierarchical, navigable, and valid road network that respects terrain and user flow.

**Key Design Standards:**
*   **Road Hierarchy:**
    *   *Ring Road (Ana Döngü):* 15-20m width. High capacity, encircles the academic core to keep traffic peripheral.
    *   *Arterial Roads (Bağlantı Yolları):* 10-12m width. Connects the ring road to major clusters (dorms, sports).
    *   *Service/Pedestrian Roads (Servis/Yaya Yolları):* 6-8m width. Restricted access, prioritizing walking/cycling.
*   **Topological Metrics (Graph Validation):**
    *   *Beta Index ($\beta$):* Measures connectivity (Edges / Nodes). Target > 1.4 for a well-connected campus.
    *   *Cyclomatic Number ($\mu$):* Measures route redundancy (Edges - Nodes + 1). Higher is better for resilience.
    *   *Alpha Index ($\alpha$):* Quantifies "meshiness" (Actual Circuits / Max Possible Circuits).
*   **Turkish Typology Alignment:**
    *   Adapting standard road profiles to typical Turkish campus scales and vehicle types (e.g., student shuttles/dolmuş).

**Algorithmic Implementation:**
*   **Graph Construction:** Nodes are building centroids + entry points; Edges are potential road segments.
*   **MST vs. Steiner Tree:** While MST (Minimum Spanning Tree) minimizes total length, a *Steiner Tree* heuristic is better for realistic infrastructure connecting multiple disparate points.
*   **Validation Function:** A fitness function that heavily penalizes unconnected graphs ($\beta < 1.0$) or excessive dead-ends.

### 6.2. GIS & Data Integration
**Key Findings:**
- **Integration Frameworks:**
    - **PostGIS + QGIS:** The "Golden Standard" for open-source spatial data management. PostGIS handles storage/querying, QGIS handles visualization/processing.
    - **Automation APIs:** `PyQGIS` (QGIS Python) and `ArcPy` (ArcGIS) automation for batch processing spatial tasks.
    - **Cloud Deployment:** Containerization (Docker) of PostGIS/QGIS workflows is standard for scalable backend services.

**Operational Optimization:**
- **Spatial Indexing:** Crucial for performance. `GiST` indexes on geometry columns in PostGIS.
- **Data Formats:** Move away from Shapefiles. Use **GeoPackage** (standard exchange) or **GeoParquet** (cloud-native, performance). `GeoJSON` for web-frontend delivery but not heavy storage.
- **Feature Service Optimization:** For ArcGIS/WebGIS, use vector tiles for base layers and feature layers only for interactive elements to reduce load.

**References:**
- *GIS Integration for Generative Planning* (Batch 4)
- *Distributed Spatial Optimization Research* (Batch 4)

---

## 7. Algorithmic Intelligence & Architectures

### 7.1. Deep Reinforcement Learning (DRL)
**Core Concepts:**
**Core Concepts:**
- **MDP Formulation:**
    - State ($S$): Canvas matrix (H x W x C) (Occupancy, Barriers) + Graph (Adjacencies).
    - Action ($A$): **Continuous coordinate pairs** $(x, y)$ (SOTA) vs Discrete Grid (Legacy).
    - Reward ($R$): **Potential-Based Reward Shaping (PBRS)** $\Phi(s)$ is required to solve sparse reward issues.
- **Algorithms:**
    - **Soft Actor-Critic (SAC):** **Recommended.** Support continuous space, high sample efficiency, and entropy regularization (prevents mode collapse).
    - **PPO:** Visual baseline, stable but data hungrier.
- **Why DRL?** Sequential decision making (placing one building at a time) matches the "construction" process better than "all-at-once" GA, allowing for reactive planning.

### 7.2. Graph Neural Networks (GNNs)
**Why GNNs?**
- **Relational Reasoning:** Buildings are nodes, relationships (adjacency, visibility, flow) are edges. Matches the "system of systems" nature of cities better than CNN grids.
- **Invariance:** **SE(2)-Equivariant GNNs** (e.g., EGNN) are critical. A layout's quality shouldn't change if rotated 90 degrees. Standard GCNs fail this; Geometric Deep Learning succeeds.

**Key Architectures:**
1.  **GCN (Graph Convolutional Networks):** Baseline isotropic averaging. Good for simple node classification but poor for complex spatial interactions.
2.  **GAT (Graph Attention Networks):** **Gold Standard for Analysis.** Uses attention mechanisms to learn *which* neighbors matter (e.g., "Dining Hall" cares more about "Dorm" affinity than "Lab").
    - *XAI Benefit:* Attention weights provide built-in explainability (e.g., visualizing which building connections lowered the score).
3.  **GraphSAGE:** **Gold Standard for Scalability.** Inductive learning allows training on small graphs (50 nodes) and generalizing to large systems (5000 nodes) without retraining.
4.  **EvolveGCN / ST-GNN:** For dynamic/phased construction. Combines GNN (spatial) with RNN (temporal) to model evolving graphs.

**Applications in Planning:**
- **Surrogate Modeling (The "Killer App"):**
    - Replacing slow physics sims (CFD, Traffic, EnergyPlus) with trained GNN predictors.
    - **Performance:** 1,000x - 10,000x speedup with >0.75 $R^2$. Enables real-time evolutionary optimization.
- **Generative Design:**
    - **GNN-GANs (e.g., House-GAN++):** Generating layouts from bubble diagrams (functional constraint graphs).
- **Link Prediction:** Predicting missing roads or utility connections.

**Implementation Stack:**
- **Library:** **PyTorch Geometric (PyG)** is recommended over DGL for physics-based tasks and integration richness.
- **Graph Construction:** Delaunay Triangulation (physically grounded) or k-NN (simple proximity).

### 7.3. Evolutionary Architectures
**Strategies:**
- **Coevolution:**
    - *Competitive:* "Generator" vs "Evaluator" (similar to GANs).
    - *Cooperative:* Decompose problem (e.g., one pop optimizes "Placement", another "Roads").
- **Distributed GA:** Island models to maintain diversity.
- **Constraint Handling:** $\epsilon$-Constrained Method and Stochastic Ranking are superior to static penalties.

### 7.4. Hybrid Optimization (H-SAGA)
**Source:** *Hybrid Optimization Algorithm Research.docx*

**The "Best of Both Worlds" Hypothesis:**
Combines **Genetic Algorithms (GA)** (Global Exploration) with **Simulated Annealing (SA)** (Local Exploitation/Refinement).
*   **Problem:** GA is great at finding the "right hill" but bad at finding the peak (premature convergence). SA is great at climbing the peak but can get stuck in the "wrong hill".
*   **Solution (Memetic/Lamarckian Model):**
    1.  GA evolves a population.
    2.  For each offspring, run a *short, high-intensity SA* to refine it to local optimality ("Maturation").
    3.  Put the *refined* individual back into the population.
*   **The "Li et al. (2025)" Inversion:** For dynamic environments, use SA for global "shocks" (high T exploration) and GA for local micro-evolution.
*   **Parameters:**
    *   **GA:** Low Crossover (0.4), High Mutation (0.1) -> Focus on *generating novelty*.
    *   **SA:** High $T_0$, Slow Cooling ($\alpha > 0.95$) -> Focus on *refining*.
*   **Complexity Warning:** Multiplicative cost $O(GA \times SA)$. **Parallelization (Master-Slave fitness)** is mandatory.

### 7.6 Surrogate-Assisted Evolutionary Algorithms (SAEA)
**Source:** `Surrogate-Assisted Evolutionary Algorithms...docx`

*   **Problem:** Physics simulations (CFD, Traffic) take minutes. Optimization needs thousands of evals.
*   **Solution:** Train cheap ML models to approximate fitness.
*   **Strategies:**
    *   **Pre-Screening:** Evolve 1000 offspring on Surrogate -> Pick Top 10 for Real Sim -> Update Surrogate.
    *   **Model Selection:**
        *   **Gaussian Process (Kriging):** Low dimensions ($D<20$), Sparse Data. Provides robust uncertainty (Infill Criteria).
        *   **Random Forest:** High dimensions ($D>50$), Robust to noise.
        *   **Graph Neural Networks (GNN):** Best for spatial topology.
*   **Speedup:** Expect **10x-50x** reduction in wall-clock time.

### 7.5. Meta-Learning & Few-Shot Adaptation
**Goal:** "Learn to Learn" - Enable rapid adaptation to new spatial tasks (e.g., a new city or project site) with minimal data (Few-Shot Learning), rather than training from scratch.

*   **Algorithms:**
    *   **MAML (Model-Agnostic Meta-Learning):** Optimizes for an initialization that can be fine-tuned quickly. *Cons:* Expensive second-order derivatives.
    *   **Reptile:** First-order approximation of MAML. Cheaper and scalable. **Recommended for initial prototypes.**
    *   **Neural Processes (NPs):** Probabilistic meta-learning. Learns a distribution over functions, providing uncertainty estimates (critical for risk assessment).
*   **Application:**
    *   **Hyperparameter Warming:** Use meta-learning to "warm-start" Bayesian Optimization (MI-SMBO) for new problems, reducing search time.
    *   **Surrogate Adaptation:** Quickly adapt a generic building energy surrogate to a specific new building design with just 5-10 simulation runs.

### 2.1 Participatory Planning & Governance
**Goal:** Legitimacy through "Citizen Control" (Arnstein's Ladder).
*   **Framework:** Move from "Tokenism" (Informing) to "Partnership" and "Citizen Control".
*   **Elicitation Methods:**
    *   **Maptionnaire:** Spatially-explicit surveys (Geo-questionnaires).
    *   **Decidim:** Deliberative democracy platform (Proposals, Debates).
    *   **CityScope:** Tangible interactive modeling (LEGO-like blocks with real-time feedback).
*   **Aggregation:**
    *   **Quadratic Voting (QV):** Captures *intensity* of preference (Vote cost = $V^2$). efficient for public goods.
    *   **Approval Voting:** Simple, avoids vote-splitting.
    *   **Machine Learning:** Active Learning to predict preferences and reduce survey fatigue.
    *   **IEC (Interactive Evolutionary Computation):** Human-in-the-loop fitness evaluation.

## 3. Data Strategy
*   **Core:** Hybrid ETL (OpenStreetMap + Official Municipality GIS).
*   **Standards:** CityJSON (Lightweight, Web-ready) > CityGML (Heavy). OGC 3D Tiles for visualization.
*   **Turkey Specific:**
    *   **IBB Open Data:** 3D Building models (LOD2), Transportation sets.
    *   **Validation:** Cross-check OSM vs. Official Cadastral Parcellation (Tapu/Kadastro).
    *   **DEM:** ALOS PALSAR 12.5m (Best free resolution for TR topography).

## 4. Generative Models (Algorithms)
*   **Core Engine:** **H-SAGA (Hybrid Spatial Alignment Genetic Algorithm)**.
*   **Road Network Generation (Hybrid):**
    *   ❌ **Pure Tensor:** Too complex (RK4, singularities) for quick implementation.
    *   ❌ **L-System:** Too chaotic, hard to control connectivity.
    *   ✅ **Basis Tensor-Guided Agents ("Turtles"):**
        *   **Global:** Pre-computed Basis Fields (Grid, Radial) blended on GPU.
        *   **Local:** Turtle Agents sample the field for *heading*, but obey local *rules* (snap, intersect, density).
        *   **Discretization:** Discrete steps avoid complex differential equation (ODE) integration.
*   **Optimization Pipeline (Bimodal):**
    *   **Phase 1 (Data-Parallel):** Tensor Field Gen -> **GPU (CuPy)**. Speedup ~100x.
    *   **Phase 2 (Task-Parallel):** Streamline Tracing -> **CPU (multiprocessing + Numba)**.
    *   **Graph:** `scipy.spatial.cKDTree` for $O(\log N)$ proximity queries.
*   **Constraint Handling:**
    *   **Hard:** Death Penalty (Infeasible = Fitness 0).
    *   **Soft:** Penalty Functions (Linear/Quadratic degradation).
*   **Spatial Field Decay Functions:**
    *   **Gaussian:** Best for residential privacy and noise buffering (localized).
    *   **Inverse Distance Weighting (IDW):** Standard for general proximity.
    *   **Power-Law (Gravity):** Best for Commercial/Retail attraction (long-tail), requires $\epsilon$-clipping.
    *   **Exponential:** Good for park influence and biological processes.
    *   **Anisotropy:** Directional decay required for wind corridors or sloped terrain.

## 5. Machine Learning Integration
*   **Surrogate Models (GNNs):**
    *   Use **Graph Neural Networks (GNNs)** to predict simulation outcomes (e.g., Wind/Solar comfort) in ms instead of minutes.
    *   Train on high-fidelity simulation data (CFD/Radiance).
*   **Deep Reinforcement Learning (DRL):**
    *   Agent-based definition of land-use changes.
    *   Good for sequential decision making (Phase 1 -> Phase 2).
*   **Meta-Learning:** MAML for few-shot adaptation to new cities.

## 6. Simulation & Analysis
*   **Solar/Shadow:** `pybdshadow` (Fast, vectorized).
*   **Wind/CFD:** `OpenFOAM` (Gold standard, slow) or ML surrogate.
*   **Traffic:** `SUMO` (Micro-simulation).
*   **Accessibility:** `Pandana` (Fast network reachability).
*   **Noise:** Simple distance-decay models vs. Ray-tracing surrogates.

## 7. Mathematical Optimization
*   **NSGA-III:** Algorithm of choice for Many-Objective (>3 objectives) problems.
*   **SAEA (Surrogate-Assisted Evolutionary Algorithm):** Critical for keeping Runtime < 30s.
    *   Use RBF (Radial Basis Functions) or Gaussian Processes (Kriging) to approximation fitness.
*   **Simulated Annealing (Hybrid Adaptive):**
    *   **Cooling:** **Fitness-Variance Cooling** ($T_{k+1} = T_k / (1 + \lambda \sigma_k)$). Slows down when variance is high.
    *   **Reheating:** Triggered by stagnation to escape local optima.
    *   **Initial Temp ($T_0$):** Set by Acceptance Ratio Heuristic (~80% acceptance).

## 8. Financial & Feasibility Models (The "Fitness Function")
**Source:** *Real Estate Development Feasibility Framework.docx*
*   **Core Concept:** A comprehensive, multi-phase **Pro Forma** integrated directly as the `calculate_fitness()` function.
*   **Negative Leverage Trap (Turkey):**
    *   TR Loan Rates (~55%) > Asset Yields (~7%).
    *   **Solution:** **USD-Denominated Pro Forma** (Hard Currency). All optimization must run in USD/EUR terms.
*   **Metrics Triad:**
    *   **IRR:** Efficiency (Hurdle > 18% USD).
    *   **Equity Multiple:** Magnitude (> 2.0x).
    *   **Cash-on-Cash:** Liquidity/Yield.
*   **Phasing Strategy:** **"Commercial First"** - Retail/Office phase builds cash flow to fund Residential equity, reducing peak capital/risk.
*   **Optimization:** NSGA-II to find **Pareto Front** of (Developer IRR vs. Public Benefit).
    *   Quantifies exact cost of public goods (e.g., "200 affordable units cost 4% IRR").

### 8.1 Social Equity & Justice (The "Social" Objective)
*   **Metrics:**
    *   **Gini Coefficient:** Minimize inequality of accessibility distribution ($G \to 0$).
    *   **Proximity-Accessibility Gap:** Distinguish between Euclidean proximity (nearby) and Network accessibility (reachable).
*   **Gentrification Paradox:** Optimization tends to maximize land value, displacing residents.
    *   *Constraint:* **Inclusionary Zoning** (Mandatory % affordable units).
    *   *Structure:* Community Land Trusts (CLT) to lock in affordability.
    *   "Social Justice" constraint: Maximize dispersion of affordable housing types.

### 8.3 Turkish Construction Cost Model (2025 Ministry Standards)
*   **The "Sınıf" (Class) System:** Official cost estimation key.
    *   **Logic:** `Building Function` -> `Sınıf` -> `Unit Cost (TL/m²)`
    *   **Mappings:**
        *   **Class V-B (35.600 TL/m²):** Hospitals, Large Faculties.
        *   **Class IV-A (21.500 TL/m²):** Standard Faculties, Apartment Blocks (>4 floors).
        *   **Class III-B (18.200 TL/m²):** Dining Halls, Dormitories.
        *   **Class V-C (39.500 TL/m²):** Large Libraries, Cultural Centers.
*   **Cost Drivers:**
    *   **Base:** 2025 "Yapı Yaklaşık Birim Maliyetleri" (Ministry of Environment).
    *   **Exclusions:** Infrastructure (Roads, Utilities) calculated separately (linear/area cost).
    *   **Inflation:** Model must support quarterly indexing.

## 9. Codebase Architecture & Standards
*   **2025 Recommended Stack (Turkish Deployment):**
    *   **Core Map Engine:** **MapLibre GL JS**. (Chosen over Mapbox v3/Google due to BSD license & localized data checks).
    *   **Drawing Engine:** **MapLibre-Geoman** (Vertex snapping, cutting, rotating).
    *   **State Management:** **Zustand + `zundo`**.
        *   *Why?* One-line Undo/Redo tracking for complex edits ("Keep/Remove" building states).
    *   **Performance:**
        *   **Web Workers:** Offload `turf.pointsWithinPolygon` for selecting 1000+ buildings.
        *   **Vector Tiles:** Use `tippecanoe` + `martin` for city-scale datasets (>10k features).
    *   **Geocoding (Turkey):** Hybrid Strategy.
        *   **Address:** **Başarsoft API** (Official UAVT valid).
        *   **POI:** **Nominatim** (Free, good for landmarks).

## 10. Visualization & Interaction
*   **Architecture:** **Hybrid Layered Stack**.
    *   **Base:** MapLibre GL JS (2D GIS, Basemap, Vector Tiles).
    *   **Context:** Deck.gl (High-perf Data Layers, 10k+ context buildings).
    *   **Interactive:** Three.js / React-Three-Fiber (R3F) (100+ High-detail plannable meshes, Shadows, Gizmos).
    *   **Sync:** Custom MapLibre layer to sync Camera Matrix with Three.js.
*   **State Management (Real-Time):**
    *   **Collaboration:** **Stateful** (Y.js CRDT) via WebSocket (ypy-websocket). Handles conflict-free co-editing.
    *   **Optimization:** **Stateless** Broadcast (FastAPI -> Redis -> Client). Handles one-way progress bars.
*   **Performance (60 FPS Mandate):**
    *   **Instancing:** Use `InstancedMesh` for repeated geometry.
    *   **Assets:** glTF (Draco compressed) > OBJ.
    *   **Shadows:** Strict culling (cascaded shadow maps), only dynamic objects cast.
*   **Accessibility (A11y):**
    *   **React-three-a11y:** Focus rings, keyboard nav for 3D canvas objects, screen reader support (ARIA descriptions).
    *   **Compliance:** WCAG 2.1 AA.

### 10.1 Scientific UI/UX Paradigms
**Source:** `Technical Planning App UI_UX Research.docx`

A scientific tool is not just a dashboard. It requires a **Hybrid Paradigm**:
1.  **Project Wizard:** Linear flow for setup (CRS, Data Import).
2.  **The Studio (Creative):** Free-form canvas (Mapbox Style).
3.  **The Dashboard (Analytical):** Comparative views (Kepler.gl Style).
4.  **The Notebook (Exploratory):** Reactive parameter scripting (Observable/Jupyter).

**Design System Choice:**
*   **Architecture:** **IBM Carbon** (Best for complex data density).
*   **Components:** **Ant Design** (Best for complex forms/inputs).
*   **Style:** **Tailwind CSS** (for layout flexibility).

## 11. Infrastructure & Hardware Optimization (Apple Silicon Focus)
*   **Environment:** Miniforge.
*   **Compute Acceleration:**
    *   **NumPy:** Force `libblas=*=*accelerate` (Conda) to use Apple AMX.
    *   **PyTorch:** Use `device="mps"` (Metal Performance Shaders) for batch tensors.
    *   **MLX:** Low-latency inference for interactive tools.
*   **Parallelism:**
    *   **Multiprocessing:** `Pool` for CPU-bound tasks (Streamlines).
    *   **QoS:** `os.setpriority` to force P-cores.
*   **Visualization:** VisPy (Local) or WebGL (Deck/Three).

## 12. Temporal Optimization & Digital Twins
*   **Phasing:** Breaking megaprojects into temporal phases ($t_0, t_1, ..., t_n$).
*   **Strategy:** **"Commercial First"** funding (Retail/Office builds cash flow for Residential equity).
*   **RHO (Rolling Horizon Optimization):** Optimize for short-term detailed ($t_0$) while keeping long-term ($t_{n}$) approx.
*   **Digital Twin & IoT:** MQTT -> InfluxDB for real-time "Actual vs Planned" feedback.

## 13. Uncertainty Quantification (UQ) & Risk
*   **Robust Optimization (RO):**
    *   **Philosophy:** Optimize for the *worst-case* scenario (Min-Max).
    *   **Uncertainty Sets:**
        *   **Box:** Interval uncertainty ($l_\infty$ norm).
        *   **Ellipsoidal:** Correlated uncertainty ($l_2$ norm) -> SOCP.
        *   **Polyhedral:** Linear inequalities -> LP.
    *   **Price of Robustness (PoR):** Trade-off curve between "Nominal Performance" and "Robustness Level".
*   **Alternative Paradigms:**
    *   **Stochastic Opt (SO):** Optimize Expected Value (risk-neutral).
    *   **Chance-Constrained (CCP):** Reliability constraints (e.g., $P(\text{fail}) < 5\%$).
    *   **Distributionally Robust (DRO):** Ambiguity set for the probability distribution itself (Wasserstein ball).
*   **Sensitivity Analysis:** Morris Method (Screening) -> Sobol Indices.
*   **Risk-Averse:** CVaR (Conditional Value-at-Risk) for robust optimization.

## 14. Quantum & Advanced Computing
**Goal:** Prepare for NP-Hard scaling (Future-Proofing).
*   **Paradigm:** **Hybrid Quantum-Classical**.
    *   **Decomposition:** Break city into "neighborhood" sub-problems.
    *   **Co-Processor:** Use Quantum (QAOA/Annealer) for hard sub-problems.
*   **Formulation:** **QUBO (Quadratic Unconstrained Binary Optimization)**.
    *   *Constraint Handling:* Penalty functions in the objective ($P(constraint)^2$).
*   **Near-Term:** **Quantum-Inspired** classical algos (Tensor Networks, SimCIM).

---

### 15. Extracted Algorithms & Metrics Reference
*(Self-contained list for quick lookup)*

*   **Financial:**
    *   *Fisher Equation:* $r_{real} = \frac{1+r_{nom}}{1+i_{inf}} - 1$
    *   *NPV:* $\sum \frac{R_t - C_t}{(1+r_{real})^t}$
*   **Spatial Analysis:**
    *   *Beta Index:* $E / V$
    *   *Cyclomatic Number:* $E - V + 1$
    *   *Space Syntax Integration:* $(D_{mean} - 1) / (D_{max} - 1)$
*   **Optimization:**
    *   *PBRS Reward:* $F(s, s') = \gamma \Phi(s') - \Phi(s)$
    *   *NSGA-II Crowding Distance:* $\sum \frac{f_{m}(i+1) - f_{m}(i-1)}{f_{m}^{max} - f_{m}^{min}}$
    *   *Steiner Tree Heuristic:* For infrastructure cost minimization.

---

## 16. Temporal Intelligence & Phasing
**Source:** *Multi-Phase Spatial Planning Optimization.docx*

### 16.1 The "When" Dimension
Optimization is not just $(x, y)$ but $(x, y, t)$. A 30-year project must be broken into phases (e.g., 0-5, 5-15, 15-30 years) to manage cash flow and disruption.
*   **Decision Variables:**
    *   $X_{b,l,p}$: Binary (Building $b$ at Location $l$ in Phase $p$).
    *   $S_{b,k}$: Sequence (Task $b$ must precede Task $k$).
*   **Operators:** Standard crossover fails on sequences. Use **Precedence-Preserving Order Crossover (POX)** to maintain logical dependencies (e.g., Foundation before Roof).

### 16.2 Rolling Horizon Optimization (RHO)
**The Strategy:** Don't plan year 30 in detail.
1.  **Optimize** full horizon (0-30).
2.  **Fix** Phase 1 (0-5) as detailed/determininstic.
3.  **Keep** Phases 2-3 as coarse/probabilistic.
4.  **Execute** Phase 1.
5.  **Re-Optimize** at Year 5 using actual data (Digital Twin feedback).

### 16.3 4D BIM & Digital Twins
*   **Visualization:** 4D BIM (Space + Time) is required to validate construction logistics (e.g., crane access shouldn't block Phase 2 site).
*   **Feedback:** Digital Twin sensors (IoT) feed "Actual vs Planned" progress back into the RHO engine for the next re-optimization cycle.

---

## 18. Benchmarking & Standardization (SPOP Suite)
*   **Architecture:** **5-Tier Hierarchy** (Synthetic Grid $\to$ Real World Digital Twin).
*   **Validation Protocol:**
    *   **Runs:** 30 Independent runs per algorithm.
    *   **Statistical Test:** Wilcoxon Rank-Sum (Non-parametric) for significance ($p < 0.05$).
*   **Metrics:**
    *   **Hypervolume (HV):** Convergence + Diversity.
    *   **IGD (Inverted Generational Distance):** Distance to True Pareto Front.
    *   **Spacing:** Uniformity of solutions.
*   **Ground Truth:** Hybrid (Objective KPIs + Expert/HCI Evaluation).

### 18.1 Turkish Campus Typologies (Benchmarking)
**Source:** `Turkish University Campus Data Benchmarking.docx`

| Typology | Example | Total Area | Green Metric |
| :--- | :--- | :--- | :--- |
| **Regional Reserve** | METU | 4,500 ha (800 ha dev) | 1,300 $m^2$/person (Forest) |
| **Compact Urban** | Boğaziçi / Koç | ~160-190 ha | N/A (Embedded) |
| **Planned Green** | ITU | N/A | 25 $m^2$/person (Managed) |

*   **Key Insight:** "Green Space" varies wildly. METU is an ecological reserve; ITU is a park. Optimization must distinguish these functional types.

### 18.2 Validation & Benchmarking Protocols
*   **The "Turkish Triad" (Flood/UHI):** 
    *   1. **Calibrate:** Manual SWMM/ENVI-met model against historic event (e.g., Ayamama 2009 Flood).
    *   2. **Validate Proxy:** Compare fast HAND/ML-Surrogate result against calibrated model.
    *   3. **Verify Design:** Run final optimized layout through SWMM/ENVI-met.

### 18.3 Competitive Landscape (Market Gap)
| Competitor | Core Focus | Architecture | PlanifyAI Diff |
| :--- | :--- | :--- | :--- |
| **Autodesk Forma** | Conceptual Massing | Cloud SaaS (Proprietary) | **Intent-Driven** (Semantic Fields vs Blackbox MOO) |
| **TestFit** | Feasibility/Yield | Desktop/Cloud Hybrid | **Holistic** (Not just parking/yield, but quality) |
| **UrbanSim** | MPO Policy Sim | Agent-Based (ABM) | **Design Tool** (Not just analysis/simulation) |
| **MIT CityScope** | Stakeholder Collab | Legos + TUI + ABM | **Digital-First** (No physical table required) |
| **Netcad** | Turkish Compliance | Desktop CAD/GIS | **Generative** (Netcad is for documentation) |

## 19. Environmental & Climate Intelligence
### 19.1 Urban Heat Island (UHI) Optimization
*   **The Challenge:** Physics models (CFD/ENVI-met) take hours; optimization needs <5s.
*   **Solution:** **ML Surrogate Models** (XGBoost / Random Forest).
    *   **Training:** Offline training on 1,000+ synthetic layouts simulated in ENVI-met.
    *   **Inputs:** GIS Proxies -> Sky View Factor (SVF), Albedo, H/W Ratio, Green Fraction, Building Density (AHF Proxy).
    *   **Inference:** < 1 second per layout.
*   **Key Thresholds:**
    *   **Tree Canopy:** >40% local coverage triggers step-change cooling (4-5°C).
    *   **SVF:** Non-linear effect; mid-density often worst (traps heat).
*   **Validation:** Landsat 8/9 LST retrieval (Mono-window algorithm) vs. Surrogate prediction. Target RMSE < 3.0K.

### 19.2 Flood Risk & Stormwater (Blue-Green)
*   **Fast Proxy (<5s):** **Height Above Nearest Drainage (HAND)**.
    *   **Concept:** Relative elevation to nearest stream.
    *   **Formula:** `Inundation = Max(0, Flood_Stage - HAND)`.
    *   **Compute:** Pre-calculated via `pysheds` (D-Infinity routing).
*   **Regulatory Constraint:** **First Flush Capture (25mm)**.
    *   **Method:** SCS-CN (Curve Number).
    *   **Requirement:** GI Volume >= Runoff from 25mm storm.
*   **Mitigation Strategy (LID):**
    *   **Green Roofs:** ~80% retention (Istanbul benchmark).
    *   **Permeable Pavement:** High infiltration, clogging risk.
    *   **Validation Case:** Ayamama Creek (Istanbul) - 2009 Flood (11m depth validation target).

## 20. Regulatory & Compliance (Turkish Standards)
### 20.1 Core Zoning Constraints (İmar Kanunu)
*   **Dynamic Setbacks:** Not static. Function of height.
    *   `Setback = Base + (Floors - 4) * 0.5m`
    *   **Implication:** Taller buildings squeeze their own buildable footprint.
    *   **High-Rise Cliff:** Above 60.50m (approx 15-20 floors), base setback jumps to 15.0m.
*   **FAR Exclusions (Emsal Harici):**
    *   **Rule:** 30% of total FAR area is "free" for Parking, Shelters, Cores.
    *   **Algo Implication:** Generator must add 30% bulk without consuming FAR budget.
*   **Emergency Access:**
    *   **Fire Rule:** Max 45m horizontal distance from fire truck access to any building point.
    *   **Graph Check:** Shortest path from road network nodes.

### 20.2 Building Taxonomy & Mappings
*   **OSM -> Turkish Sınıf Heuristic:**
    *   `amenity=cafe` + `landuse=university` -> **Yemekhane (III-B)**
    *   `building=dormitory` -> **Yurt (III-B/IV-B)**
    *   `amenity=library` (University) -> **Kütüphane (V-C)**
    *   `building=university` -> **Fakülte (IV-A)**

### 20.3 Turkish Address & Geocoding
*   **Constraint:** Google Maps API prohibited on non-Google maps. OSM (Nominatim) address quality in Turkey is poor.
*   **Solution:** **Başarsoft GeoCoder**.
    *   Aligned with **UAVT** (National Address Database).
    *   Required for finding specific parcels/streets legally.

### 20.4 Additional Regulatory Intelligence
*   **Earthquake (Deprem):**
    *   **TBDY 2018:** Turkey Building Earthquake Code.
    *   **AFAD Hazard Maps:** PGA (Peak Ground Acceleration) integration.
*   **Solar Rights:** "Gunes Erisim Hakki" - ensuring new high-rises don't shadow existing low-rises (uses `pybdshadow`).
*   **Patent Strategy (Critical):**
    *   **Pivot:** "Tensor Fields + MOO" is NOT patentable (Prior Art: ArXiv:2212.06783).
    *   **Novelty:** The **Dynamic Feedback Loop (DFL)** (Bidirectional: Roads <-> Buildings).
    *   **Filing Path:** **TR National Patent** (Method) -> **PCT**. *Avoid Utility Model (Software excluded).*

## 21. Utility Network Intelligence (Co-Optimization)
*   **The "Chicken-and-Egg" Problem:** Optimal infrastructure depends on building layout, but optimal layout depends on infrastructure cost.
*   **Algorithms:**
    *   **Minimum Spanning Tree (MST):** Lowest cost connectivity (Radial Networks).
        *   *Library:* `networkx.minimum_spanning_tree`.
    *   **Steiner Tree:** Optimal corridors for subset of points (NP-Hard approximation).
        *   *Library:* `networkx.approximation.steiner_tree`.
    *   **Max Flow / Min Cut:** Capacity analysis.
*   **Hydraulics (Water/Sewer):**
    *   **Constraint:** Gravity sewers need min slope (0.5%) -> Topography drives cost.
    *   **Simulation:** **EPANET** (via `wntr` or `epanet-python`).
        *   *Check:* Pressure (20-80 psi), Velocity (Self-cleansing).

## 22. Explainable AI (XAI) & Engagement
### 22.1 Immersive Engagement (VR/AR)
*   **Hierarchy of Immersion:**
    *   **WebXR:** Broadest reach (Browser-based). Public consultation.
    *   **Mobile AR:** On-site visualization (Massing/Shadows).
    *   **Full VR:** Expert design review / Stakeholder workshops.
*   **Motion Sickness Protocol:**
    *   **Movement:** **Teleportation ONLY**. No smooth locomotion (joystick walking).
    *   **Refresh Rate:** strict >90Hz.
    *   **Vignetting:** Dynamic FOV reduction during movement.

### 22.2 Explaining the "Black Box" (XAI)
*   **Why?** Stakeholders distrust "AI-generated" plans without rationale.
*   **Techniques:**
    *   **SHAP (SHapley Additive exPlanations):** Global feature importance ("Green space contributed 40% to this score").
    *   **LIME:** Local explanation ("This specific building is tall because of X constraint").
    *   **Counterfactuals:** "If you want +10% density, you must sacrifice Y% Walkability."
*   **Implementation:** `shap`, `dice-ml` (Counterfactuals).

## 23. Processed Document Tracker

| Batch | File Name | Key Contribution | Status |
|-------|-----------|------------------|--------|
| 1 | 15-Minute City Optimization Analysis.docx | Turkish-specific urban metrics, Decay functions | ✅ Extracted |
| 1 | 3D Urban Design Optimization Analysis.docx | Tensor field math, Vertical urbanism | ✅ Extracted |
| 1 | Adaptive Planning Through POE.docx | RL Reward function, Data-driven design loop | ✅ Extracted |
| 1 | Adaptive RK4 Streamline Generation.docx | `scipy.integrate.RK45` guide, Stopping criteria | ✅ Extracted |
| 1 | Automated Building Code Compliance.docx | Hybrid SHACL/Python engine, Turkish Code Hierarchy | ✅ Extracted |
| 2 | BIM Integration for AI Planning.docx | Hybrid Revit/IfcOpenShell Architecture, ETL-F Pipeline | ✅ Extracted |
| 2 | Building Energy Modeling Integration... | EnergyPlus/OpenStudio workflow, Surrogate modeling | ✅ Extracted |
| 2 | Building Typology Spatial Optimization... | QAP for Adjacency, MILP for Coverage, NSGA-III | ✅ Extracted |
| 2 | Campus Planning Standards and Metrics.docx | ADA-Calibrated 2SFCA, Universal Design Principles | ✅ Extracted |
| 2 | Campus Road Network Research & Design.docx | Turkish Campus Archetypes (METU/Boğaziçi), Network Metrics | ✅ Extracted |
| 3 | Construction Cost and NPV Optimization... | LCCA, Real Discount Rates, Fisher Equation | ✅ Extracted |
| 3 | DRL for Spatial Planning... | MDP Formulation, SAC, PBRS, Hybrid State | ✅ Extracted |
| 4 | GIS Integration... | (Merged into Pillar 9) | ✅ Extracted |
| 4 | Distributed Spatial Optimization... | (Merged into Pillar 7) | ✅ Extracted |
| 4 | Graph Neural Networks for Spatial... | GAT, SE(2)-Equivariance, Surrogate Modeling | ✅ Extracted |
| 5 | Campus_Urban Planning Patent Search... | Patentability of Semantic-Tensor Hybrids | ✅ Extracted |
| 5 | Carbon Footprint Optimization... | Net-Zero Logic, Life Cycle Carbon formulas | ✅ Extracted |
| 5 | Coevolutionary Algorithms... | (merged into 7.3/7.4) | ✅ Extracted |
| 5 | Geospatial Data for Campus Planning.docx | Turkey Data Sources (IBB/OSM), Hybrid ETL | ✅ Extracted |
| 5 | Geospatial Data for Urban Planning.docx | Detailed Data Strategy, DEM Selection | ✅ Extracted |
| 5 | Hybrid Optimization Algorithm Research.docx | H-SAGA Framework, Memetic Algorithms | ✅ Extracted |
| 25 | IoT Spatial Planning Optimization Research.docx | Digital Twins, IoT, MQTT | ✅ Extracted |
| 26 | M1 Python Scientific Computing Optimization.docx | Apple Silicon, Accelerate, VisPy | ✅ Extracted |
| 27 | Meta-Learning for Spatial Planning Adaptation.docx | MAML, Reptile, Few-Shot | ✅ Extracted |
| 28 | Monte Carlo for Spatial Planning Uncertainty.docx | UQ, Sobol Sequence, CVaR | ✅ Extracted |
| 29 | Multi-Objective Evolutionary Algorithms... | NSGA-III Guide, SAEA for Speed | ✅ Extracted |
| 30 | Multi-Objective Spatial Planning Research... | Case Studies, AHP-TOPSIS Workflow | ✅ Extracted |
| 31 | Multi-Phase Spatial Planning Optimization.docx | RHO, 4D BIM, ROA | ✅ Extracted |
| 33 | Participatory Planning Preference.docx | QV, Maptionnaire, Arnstein| ✅ Extracted |
| 34 | Patent Analysis for Tensor Field Planning.docx | DFL Pivot, TR Strategy | ✅ Extracted |
| 35 | Quantum Optimization for Spatial Planning.docx | QUBO, QAOA, Hybrid | ✅ Extracted |
| 36 | Real Estate Development Feasibility.docx | USD Pro Forma, Fitness Fn| ✅ Extracted |
| 41 | Real-Time 3D Spatial Planning Studio.docx | Hybrid (Map+3D), Y.js | ✅ Extracted |
| 42 | Real-Time Road Network Generation Optimization.docx | Hybrid (GPU/CPU), Numba | ✅ Extracted |
| 43 | Robust Optimization for Spatial Planning.docx | RO, Uncertainty Sets, PoR| ✅ Extracted |
| 44 | Simplified Road Network Generation Research.docx | Hybrid (Tensor+Agent) | ✅ Extracted |
| 45 | Simulated Annealing Cooling Schedules Comparison.docx | Adaptive Cooling, Fitness-Variance | ✅ Extracted |
| 46 | Spatial Equity and Gini Optimization.docx | Gini Index, Gentrification Paradox | ✅ Extracted |
| 47 | Spatial Influence Decay Functions Analysis.docx | Gaussian vs Power-law, Anisotropy | ✅ Extracted |
| 48 | Spatial Planning Benchmark Dataset Framework.docx | SPOP Suite, 5-Tier Benchmarking | ✅ Extracted |
| 49 | Tensor Field Singularity Detection Analysis.docx | Wedges, Trisectors, Root Finding | ✅ Extracted |
| 50 | Traffic Microsimulation for Spatial Planning.docx | SUMO, MATSim, SITL Framework | ✅ Extracted |
| 51 | Transfer Learning in Spatial Planning.docx | DANN, Domain Shift (Campus -> Industrial) | ✅ Extracted |
| 52 | Turkish University Campus Data Benchmarking.docx | METU, Boğaziçi, ITU Metrics | ✅ Extracted |
| 53 | Turkish Urban Planning Standards Research.docx | Dynamic Setbacks, FAR Exclusions, Fire Access | ✅ Extracted |
| 54 | UHI Modeling for Urban Planning Optimization.docx | ML Surrogate, SVF, Albedo, Canopy | ✅ Extracted |
| 55 | Urban Flood Risk and Stormwater Optimization.docx | HAND, SCS-CN, Ayamama Validation | ✅ Extracted |
| 56 | Urban Planning Tool Competitive Analysis.docx | Forma, TestFit, Semantic Field Positioning | ✅ Extracted |
| 57 | Urban Planning Tool Research Report.docx | MapLibre, Geoman, Zustand-Zundo, Başarsoft | ✅ Extracted |
| 58 | Utility Network Optimization Research Plan.docx | MST, Steiner Trees, EPANET Integration | ✅ Extracted |
| 59 | VR_AR for Spatial Planning Engagement.docx | WebXR vs VR, Motion Sickness Protocols | ✅ Extracted |
| 60 | XAI for Spatial Planning Optimization.docx | SHAP, LIME, Counterfactuals, Trust | ✅ Extracted |
| 13 | Street Network Generation Research.docx | Comparison of L-Systems vs Tensors | ✅ Extracted |
| 13 | Surrogate-Assisted Evolutionary Algorithms... | SAEA Strategies, Infill Criteria | ✅ Extracted |
| 13 | Technical Planning App UI_UX Research.docx | Hybrid Studio/Dashboard UX | ✅ Extracted |
| 13 | Tensor Field Road Generation Guide.docx | RK45 Implementation, Python Stack | ✅ Extracted |
| 13 | Tensor Field Road Network Generation.docx | Mathematical Foundation (Singularities) | ✅ Extracted |
