# Optimization Landscape Analysis & Strategy

**Date:** 2025-12-10
**Context:** Systemic review of advanced optimization methodologies for PlanifyAI's spatial planning engine.
**Documents Reviewed:**
1. `temp_moea.txt` (NSGA-III vs MOEA/D)
2. `temp_hybrid.txt` (H-SAGA)
3. `temp_sa.txt` (SA Cooling Schedules)
4. `temp_drl.txt` (Deep Reinforcement Learning)
5. `temp_coevo.txt` (Coevolutionary Algorithms)

---

## 1. Multi-Objective Evolutionary Algorithms (MOEAs)

### NSGA-III vs. MOEA/D
| Feature | NSGA-III | MOEA/D |
| :--- | :--- | :--- |
| **Core Mechanism** | Reference-point based non-dominated sorting | Decomposition into scalar subproblems (Tchebycheff) |
| **Pareto Front** | Robust to non-uniform/disconnected fronts | Sensitive to shape; struggles with complex fronts |
| **Complexity** | $O(MN^2)$ | $O(MNT)$ (generally faster) |
| **Normalization** | Internal/Adaptive | Requires external/manual normalization |
| **Recommendation** | **PRIMARY CHOICE** for Campus Planning | Alternative only if speed is critical and PF is convex |

**Decision:** Adopt **NSGA-III** as the baseline multi-objective solver. Its ability to handle "messy" Pareto fronts characteristic of spatial planning (disconnected feasible regions) trumps MOEA/D's speed advantage.

---

## 2. Hybrid Approaches (H-SAGA)

**Concept:** Combine Genetic Algorithms (global search) with Simulated Annealing (local refinement).
**Architecture:**
*   **Collaborative:** Sequential or parallel exchange of partial solutions.
*   **Integrative (Memetic):** SA acts as a mutation operator within GA.

**Key Insight:** While H-SAGA offers a balance, it introduces a high parameter tuning burden ($T_0, \alpha$ for SA + $P_c, P_m$ for GA).
**Strategy:** Use **Memetic Algorithm** principles. Instead of a full H-SAGA, implement a "Smart Mutation" operator in NSGA-III that utilizes a short-burst, adaptive SA or local search.

---

## 3. Simulated Annealing (SA) Cooling Schedules

**Analysis of Schedules:**
*   *Exponential/Linear:* Too rigid for complex spatial constraints.
*   *Adaptive:* Essential for robustness.

**Recommended Strategy:**
1.  **Initial Temp ($T_0$):** Determine via Acceptance Ratio heuristic (start high enough to accept 80% of bad moves).
2.  **Cooling:** Fitness-Variance based (slow down cooling when variance is high/phase transition).
3.  **Reheating:** Cost-based reheating to escape deep local optima.

**Implementation:** Apply this adaptive schedule to the "Smart Mutation" operator mentioned above, or when running SA in isolation for specific sub-problems (e.g., road network routing).

---

## 4. Deep Reinforcement Learning (DRL)

**Role:** Sequential decision making (e.g., placing buildings one by one), enabling "learned intuition".
**Algorithm:** **Soft Actor-Critic (SAC)**.
*   *Why:* Off-policy (sample efficient), continuous action space support, maximum entropy framework (better exploration).

**Architecture:**
*   **State:** Hybrid Multi-Modal
    *   **Grid (CNN):** Terrain, simplified layout.
    *   **Graph (GNN):** Road topology, building relationships.
    *   **Vector (MLP):** Global context (budget, constraints).
*   **Reward:** **Potential-Based Reward Shaping (PBRS)**. Crucial for converting sparse "final layout quality" into dense step-by-step signals without altering optimal policy.

**Status:** High risk, high reward. Long-term goal.

---

## 5. Coevolutionary Algorithms (CoEA)

**Role:** Robustness and Dynamic Environments.
*   **Competitive:** Optimizer vs. Constraints (Red Queen Effect). Useful for finding robust solutions against changing requirements.
*   **Cooperative:** Decompose campus into zones/phases. Sub-populations evolve independently but are evaluated together.

**Strategy:** Use **Cooperative Coevolution** for scaling. If the campus > 100 buildings, decompose by functional zones (Residential Zone Solver + Academic Zone Solver).

---

## Synthesis & Implementation Roadmap

### Phase 1: The Robust Baseline (Current Focus)
*   **Algorithm:** **NSGA-III**
*   **Library:** `pymoo`
*   **Augmentation:** Adaptive Reference Points.

### Phase 2: Hybrid Reinforcement (Next Step)
*   **Mechanism:** Memetic Improvement.
*   **Action:** Implement a custom mutation operator for NSGA-III that runs a short **Adaptive SA** chain on the individual.

### Phase 3: The Learning Agent (Future)
*   **Algorithm:** **SAC**
*   **Focus:** Training an agent to *initialize* the population for Phase 1/2, drastically reducing convergence time.

### Phase 4: Scale (Large Scale)
*   **Mechanism:** Cooperative Coevolution.
*   **Action:** Decompose the master plan into sub-problems passed to instances of the Phase 2 solver.
