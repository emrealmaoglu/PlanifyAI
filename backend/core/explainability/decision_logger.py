"""
Decision Logger for Optimization Explainability
================================================

Logs algorithmic decisions to explain WHY the optimizer made specific choices.

Key Features:
    - Records parameter selections (temperature, mutation rate, etc.)
    - Logs operator choices (which crossover/mutation used)
    - Tracks solution acceptance/rejection reasoning
    - Provides timeline of optimization decisions
    - Enables post-hoc analysis and debugging

Use Cases:
    - User asks: "Why was building X placed here?"
    - Developer debugging: "Why did GA get stuck?"
    - Performance analysis: "Which operators worked best?"

References:
    - XAI: Transparency through decision provenance
    - Research: "Explainable AI Campus Planning.docx"

Created: 2026-01-01
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class DecisionType(Enum):
    """Types of algorithmic decisions to log."""

    # Algorithm phase
    PHASE_START = "phase_start"  # SA or GA phase started
    PHASE_END = "phase_end"  # Phase completed

    # Parameter selection
    PARAMETER_SET = "parameter_set"  # Temperature, pop size, etc.
    PARAMETER_ADAPT = "parameter_adapt"  # Adaptive parameter change

    # Operator selection
    OPERATOR_CHOICE = "operator_choice"  # Which crossover/mutation chosen
    OPERATOR_RESULT = "operator_result"  # Operator success/failure

    # Solution evaluation
    SOLUTION_ACCEPTED = "solution_accepted"  # Solution accepted (SA/GA)
    SOLUTION_REJECTED = "solution_rejected"  # Solution rejected
    SOLUTION_IMPROVED = "solution_improved"  # New best found

    # Constraint handling
    CONSTRAINT_VIOLATED = "constraint_violated"  # Hard constraint failed
    CONSTRAINT_SATISFIED = "constraint_satisfied"  # Constraint passed

    # Objective trade-off
    TRADEOFF_DECISION = "tradeoff_decision"  # Multi-objective choice made

    # Termination
    CONVERGENCE = "convergence"  # Algorithm converged
    TIMEOUT = "timeout"  # Time limit reached
    MAX_ITERATIONS = "max_iterations"  # Iteration limit reached


@dataclass
class OptimizerDecision:
    """
    Record of a single optimizer decision.

    Attributes:
        timestamp: When decision was made
        decision_type: Type of decision
        phase: Algorithm phase (SA/GA)
        iteration: Iteration number
        description: Human-readable description
        reasoning: WHY this decision was made
        data: Supporting data (fitness, parameters, etc.)
        outcome: Result of this decision (if applicable)
    """

    timestamp: datetime
    decision_type: DecisionType
    phase: str  # "SA" or "GA"
    iteration: int
    description: str
    reasoning: str
    data: Dict[str, Any] = field(default_factory=dict)
    outcome: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "type": self.decision_type.value,
            "phase": self.phase,
            "iteration": self.iteration,
            "description": self.description,
            "reasoning": self.reasoning,
            "data": self.data,
            "outcome": self.outcome,
        }


class DecisionLogger:
    """
    Logs optimization decisions for explainability.

    Usage:
        >>> logger = DecisionLogger()
        >>> logger.log_phase_start("SA", temperature=1000.0)
        >>> logger.log_solution_accepted(fitness=0.75, reason="Metropolis")
        >>> timeline = logger.get_timeline()
        >>> logger.export_to_json("decisions.json")
    """

    def __init__(self, max_decisions: int = 10000):
        """
        Initialize decision logger.

        Args:
            max_decisions: Maximum decisions to store (prevent memory issues)
        """
        self.decisions: List[OptimizerDecision] = []
        self.max_decisions = max_decisions
        self.current_phase = "INIT"
        self.current_iteration = 0

    def log(
        self,
        decision_type: DecisionType,
        description: str,
        reasoning: str,
        data: Optional[Dict[str, Any]] = None,
        outcome: Optional[str] = None,
    ):
        """
        Log a decision.

        Args:
            decision_type: Type of decision
            description: Short description (what happened)
            reasoning: Explanation (why it happened)
            data: Supporting data
            outcome: Result of decision
        """
        decision = OptimizerDecision(
            timestamp=datetime.now(),
            decision_type=decision_type,
            phase=self.current_phase,
            iteration=self.current_iteration,
            description=description,
            reasoning=reasoning,
            data=data or {},
            outcome=outcome,
        )

        self.decisions.append(decision)

        # Prevent unbounded growth
        if len(self.decisions) > self.max_decisions:
            # Keep first 1000 and last (max_decisions - 1000)
            keep_first = 1000
            keep_last = self.max_decisions - keep_first
            self.decisions = self.decisions[:keep_first] + self.decisions[-keep_last:]

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    def log_phase_start(self, phase: str, **params):
        """Log start of optimization phase (SA/GA)."""
        self.current_phase = phase
        self.current_iteration = 0

        self.log(
            DecisionType.PHASE_START,
            description=f"{phase} phase started",
            reasoning=f"Beginning {phase} optimization with configured parameters",
            data=params,
        )

    def log_phase_end(self, phase: str, n_solutions: int, best_fitness: float):
        """Log end of optimization phase."""
        self.log(
            DecisionType.PHASE_END,
            description=f"{phase} phase completed",
            reasoning=f"Generated {n_solutions} solutions, best fitness: {best_fitness:.4f}",
            data={
                "phase": phase,
                "n_solutions": n_solutions,
                "best_fitness": best_fitness,
            },
        )

    def log_parameter_set(self, param_name: str, value: Any, reasoning: str):
        """Log parameter configuration."""
        self.log(
            DecisionType.PARAMETER_SET,
            description=f"Set {param_name} = {value}",
            reasoning=reasoning,
            data={"parameter": param_name, "value": value},
        )

    def log_parameter_adapt(self, param_name: str, old_value: Any, new_value: Any, reasoning: str):
        """Log adaptive parameter change."""
        self.log(
            DecisionType.PARAMETER_ADAPT,
            description=f"Adapted {param_name}: {old_value} → {new_value}",
            reasoning=reasoning,
            data={"parameter": param_name, "old_value": old_value, "new_value": new_value},
        )

    def log_operator_choice(self, operator_name: str, reasoning: str):
        """Log operator selection (crossover/mutation)."""
        self.log(
            DecisionType.OPERATOR_CHOICE,
            description=f"Selected operator: {operator_name}",
            reasoning=reasoning,
            data={"operator": operator_name},
        )

    def log_solution_accepted(
        self,
        fitness: float,
        reason: str,
        delta_fitness: Optional[float] = None,
        acceptance_prob: Optional[float] = None,
    ):
        """Log solution acceptance."""
        data = {"fitness": fitness}
        if delta_fitness is not None:
            data["delta_fitness"] = delta_fitness
        if acceptance_prob is not None:
            data["acceptance_prob"] = acceptance_prob

        self.log(
            DecisionType.SOLUTION_ACCEPTED,
            description=f"Accepted solution (fitness={fitness:.4f})",
            reasoning=reason,
            data=data,
            outcome="ACCEPTED",
        )

    def log_solution_rejected(
        self,
        fitness: float,
        reason: str,
        delta_fitness: Optional[float] = None,
        acceptance_prob: Optional[float] = None,
    ):
        """Log solution rejection."""
        data = {"fitness": fitness}
        if delta_fitness is not None:
            data["delta_fitness"] = delta_fitness
        if acceptance_prob is not None:
            data["acceptance_prob"] = acceptance_prob

        self.log(
            DecisionType.SOLUTION_REJECTED,
            description=f"Rejected solution (fitness={fitness:.4f})",
            reasoning=reason,
            data=data,
            outcome="REJECTED",
        )

    def log_solution_improved(self, old_fitness: float, new_fitness: float):
        """Log new best solution found."""
        improvement = new_fitness - old_fitness
        improvement_pct = (improvement / max(abs(old_fitness), 1e-10)) * 100

        self.log(
            DecisionType.SOLUTION_IMPROVED,
            description=f"New best solution found (fitness={new_fitness:.4f})",
            reasoning=(
                f"Improvement of {improvement:.4f} ({improvement_pct:.2f}%) "
                f"over previous best ({old_fitness:.4f})"
            ),
            data={
                "old_fitness": old_fitness,
                "new_fitness": new_fitness,
                "improvement": improvement,
                "improvement_percent": improvement_pct,
            },
            outcome="NEW_BEST",
        )

    def log_constraint_violated(self, constraint_name: str, violation_amount: float):
        """Log constraint violation."""
        self.log(
            DecisionType.CONSTRAINT_VIOLATED,
            description=f"Constraint violated: {constraint_name}",
            reasoning=f"Violation amount: {violation_amount:.4f}",
            data={"constraint": constraint_name, "violation": violation_amount},
        )

    def log_tradeoff_decision(
        self,
        objective1: str,
        value1: float,
        objective2: str,
        value2: float,
        chosen_solution: str,
        reasoning: str,
    ):
        """Log multi-objective trade-off decision."""
        self.log(
            DecisionType.TRADEOFF_DECISION,
            description=f"Trade-off: {objective1} vs {objective2}",
            reasoning=reasoning,
            data={
                "objective1": objective1,
                "value1": value1,
                "objective2": objective2,
                "value2": value2,
                "chosen": chosen_solution,
            },
            outcome=chosen_solution,
        )

    def log_convergence(self, reason: str, final_fitness: float):
        """Log algorithm convergence."""
        self.log(
            DecisionType.CONVERGENCE,
            description="Algorithm converged",
            reasoning=reason,
            data={"final_fitness": final_fitness},
            outcome="CONVERGED",
        )

    def increment_iteration(self):
        """Increment current iteration counter."""
        self.current_iteration += 1

    # =========================================================================
    # REPORTING AND EXPORT
    # =========================================================================

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Get chronological timeline of all decisions."""
        return [d.to_dict() for d in self.decisions]

    def get_decisions_by_type(self, decision_type: DecisionType) -> List[OptimizerDecision]:
        """Get all decisions of a specific type."""
        return [d for d in self.decisions if d.decision_type == decision_type]

    def get_decisions_by_phase(self, phase: str) -> List[OptimizerDecision]:
        """Get all decisions from a specific phase."""
        return [d for d in self.decisions if d.phase == phase]

    def get_summary(self) -> Dict[str, Any]:
        """Generate summary statistics."""
        if not self.decisions:
            return {"total_decisions": 0}

        # Count by type
        by_type = {}
        for decision_type in DecisionType:
            count = len(self.get_decisions_by_type(decision_type))
            if count > 0:
                by_type[decision_type.value] = count

        # Count by phase
        by_phase = {}
        for d in self.decisions:
            by_phase[d.phase] = by_phase.get(d.phase, 0) + 1

        # Count outcomes
        outcomes = {}
        for d in self.decisions:
            if d.outcome:
                outcomes[d.outcome] = outcomes.get(d.outcome, 0) + 1

        # Timeline stats
        if len(self.decisions) >= 2:
            duration = (self.decisions[-1].timestamp - self.decisions[0].timestamp).total_seconds()
        else:
            duration = 0.0

        # Find improvements
        improvements = self.get_decisions_by_type(DecisionType.SOLUTION_IMPROVED)
        n_improvements = len(improvements)

        # Best fitness achieved
        best_fitness = None
        if improvements:
            best_fitness = improvements[-1].data.get("new_fitness")

        return {
            "total_decisions": len(self.decisions),
            "decisions_by_type": by_type,
            "decisions_by_phase": by_phase,
            "outcomes": outcomes,
            "duration_seconds": duration,
            "n_improvements": n_improvements,
            "best_fitness": best_fitness,
            "phases": list(by_phase.keys()),
        }

    def generate_text_report(self) -> str:
        """Generate human-readable text report."""
        summary = self.get_summary()

        lines = []
        lines.append("=" * 80)
        lines.append("OPTIMIZATION DECISION LOG")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Total Decisions: {summary['total_decisions']}")
        lines.append(f"Duration: {summary.get('duration_seconds', 0):.2f}s")
        lines.append(f"Phases: {', '.join(summary.get('phases', []))}")
        lines.append("")

        if summary.get("best_fitness") is not None:
            lines.append(f"Best Fitness Achieved: {summary['best_fitness']:.4f}")
            lines.append(f"Number of Improvements: {summary['n_improvements']}")
            lines.append("")

        lines.append("DECISION BREAKDOWN:")
        lines.append("-" * 80)
        for dtype, count in summary.get("decisions_by_type", {}).items():
            lines.append(f"  {dtype:30s} {count:6d}")

        lines.append("")
        lines.append("RECENT DECISIONS (Last 10):")
        lines.append("-" * 80)

        for d in self.decisions[-10:]:
            lines.append(f"\n[{d.phase}:{d.iteration}] {d.decision_type.value}")
            lines.append(f"  {d.description}")
            lines.append(f"  → {d.reasoning}")
            if d.outcome:
                lines.append(f"  ⟹ {d.outcome}")

        lines.append("")
        lines.append("=" * 80)

        return "\n".join(lines)

    def export_to_json(self, filepath: str):
        """Export decisions to JSON file."""
        import json

        data = {
            "summary": self.get_summary(),
            "timeline": self.get_timeline(),
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def clear(self):
        """Clear all decisions."""
        self.decisions = []
        self.current_phase = "INIT"
        self.current_iteration = 0
