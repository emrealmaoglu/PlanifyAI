"""
AI Critique System for Campus Layout Analysis.

Uses local Ollama (Llama 3.2 3B) to provide intelligent feedback
on generated campus layouts. Analyzes urban design quality and
suggests improvements.

CRITICAL: Must set keep_alive=0 to free M1 RAM after use!
"""

import json
import requests
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from shapely.geometry import Polygon, Point

from backend.core.integration.building_geometry import BuildingGene, BuildingType


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class CritiqueConfig:
    """Configuration for AI critique system."""
    
    # Ollama settings
    ollama_host: str = "http://localhost:11434"
    model_name: str = "llama3.2:3b"
    
    # CRITICAL: Set to 0 to unload model after use (M1 RAM protection)
    keep_alive: int = 0  # Seconds to keep model in memory (0 = unload immediately)
    
    # Request settings
    timeout: int = 120  # seconds
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # Analysis settings
    enable_detailed_analysis: bool = True
    include_suggestions: bool = True
    
    # Fallback
    use_fallback_on_error: bool = True


class CritiqueAspect(Enum):
    """Aspects of layout to critique."""
    SPATIAL_EFFICIENCY = "spatial_efficiency"
    CIRCULATION = "circulation"
    BUILDING_RELATIONSHIPS = "building_relationships"
    ENVIRONMENTAL = "environmental"
    ACCESSIBILITY = "accessibility"
    AESTHETICS = "aesthetics"


# =============================================================================
# LAYOUT ANALYZER
# =============================================================================

@dataclass
class LayoutMetrics:
    """Extracted metrics from a layout."""
    
    # Basic counts
    num_buildings: int
    total_footprint_area: float  # m²
    site_area: float  # m²
    coverage_ratio: float  # 0-1
    
    # Building distribution
    building_types: Dict[str, int]
    avg_building_size: float  # m²
    size_variance: float
    
    # Spatial metrics
    avg_building_separation: float  # meters
    min_building_separation: float
    max_building_separation: float
    
    # Compactness
    centroid: Tuple[float, float]
    spread_radius: float  # meters
    compactness_score: float  # 0-1
    
    # Alignment
    dominant_orientation: float  # degrees
    orientation_consistency: float  # 0-1
    
    # Objective values (from optimizer)
    overlap_penalty: float
    solar_penalty: float
    wind_penalty: float
    constraint_violations: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "num_buildings": self.num_buildings,
            "total_footprint_area": round(self.total_footprint_area, 1),
            "site_area": round(self.site_area, 1),
            "coverage_ratio": round(self.coverage_ratio, 3),
            "building_types": self.building_types,
            "avg_building_size": round(self.avg_building_size, 1),
            "size_variance": round(self.size_variance, 1),
            "avg_building_separation": round(self.avg_building_separation, 1),
            "min_building_separation": round(self.min_building_separation, 1),
            "max_building_separation": round(self.max_building_separation, 1),
            "centroid": (round(self.centroid[0], 1), round(self.centroid[1], 1)),
            "spread_radius": round(self.spread_radius, 1),
            "compactness_score": round(self.compactness_score, 3),
            "dominant_orientation": round(self.dominant_orientation, 1),
            "orientation_consistency": round(self.orientation_consistency, 3),
            "overlap_penalty": round(self.overlap_penalty, 2),
            "solar_penalty": round(self.solar_penalty, 2),
            "wind_penalty": round(self.wind_penalty, 2),
            "constraint_violations": round(self.constraint_violations, 2)
        }


class LayoutAnalyzer:
    """
    Analyzes a campus layout and extracts metrics for AI critique.
    """
    
    def __init__(self, site_boundary: Polygon = None):
        self.site_boundary = site_boundary
    
    def analyze(
        self,
        genes: List[BuildingGene],
        polygons: List[Polygon],
        objective_values: Dict[str, float] = None
    ) -> LayoutMetrics:
        """
        Analyze a layout and extract metrics.
        
        Args:
            genes: List of BuildingGene objects
            polygons: List of building polygons
            objective_values: Objective values from optimizer
            
        Returns:
            LayoutMetrics object
        """
        if not genes or not polygons:
            raise ValueError("Must provide genes and polygons")
        
        n = len(genes)
        
        # Basic metrics
        footprints = [p.area for p in polygons]
        total_footprint = sum(footprints)
        site_area = self.site_boundary.area if self.site_boundary else 200000  # Default 200k m²
        coverage = total_footprint / site_area
        
        # Building types
        type_counts = {}
        for gene in genes:
            tname = gene.building_type.name
            type_counts[tname] = type_counts.get(tname, 0) + 1
        
        # Size metrics
        avg_size = np.mean(footprints)
        size_var = np.std(footprints)
        
        # Separation metrics
        separations = []
        for i in range(n):
            for j in range(i + 1, n):
                dist = polygons[i].distance(polygons[j])
                separations.append(dist)
        
        if separations:
            avg_sep = np.mean(separations)
            min_sep = np.min(separations)
            max_sep = np.max(separations)
        else:
            avg_sep = min_sep = max_sep = 0
        
        # Centroid and spread
        centroids = np.array([(p.centroid.x, p.centroid.y) for p in polygons])
        mean_centroid = centroids.mean(axis=0)
        distances_from_center = np.sqrt(((centroids - mean_centroid) ** 2).sum(axis=1))
        spread = np.max(distances_from_center)
        
        # Compactness (ratio of actual spread to theoretical minimum)
        theoretical_min_spread = np.sqrt(total_footprint / np.pi)
        compactness = min(1.0, theoretical_min_spread / (spread + 1))
        
        # Orientation analysis
        orientations = [gene.orientation for gene in genes]
        orientations_deg = [np.degrees(o) % 180 for o in orientations]  # Normalize to 0-180
        
        # Dominant orientation (circular mean)
        sin_sum = sum(np.sin(2 * np.radians(o)) for o in orientations_deg)
        cos_sum = sum(np.cos(2 * np.radians(o)) for o in orientations_deg)
        dominant_orient = (np.degrees(np.arctan2(sin_sum, cos_sum)) / 2) % 180
        
        # Orientation consistency
        orient_diffs = [min(abs(o - dominant_orient), 180 - abs(o - dominant_orient)) 
                       for o in orientations_deg]
        orient_consistency = 1 - (np.mean(orient_diffs) / 45)  # 45° max diff
        orient_consistency = max(0, min(1, orient_consistency))
        
        # Objective values
        obj = objective_values or {}
        
        return LayoutMetrics(
            num_buildings=n,
            total_footprint_area=total_footprint,
            site_area=site_area,
            coverage_ratio=coverage,
            building_types=type_counts,
            avg_building_size=avg_size,
            size_variance=size_var,
            avg_building_separation=avg_sep,
            min_building_separation=min_sep,
            max_building_separation=max_sep,
            centroid=tuple(mean_centroid),
            spread_radius=spread,
            compactness_score=compactness,
            dominant_orientation=dominant_orient,
            orientation_consistency=orient_consistency,
            overlap_penalty=obj.get("overlap", 0),
            solar_penalty=obj.get("solar", 0),
            wind_penalty=obj.get("wind", 0),
            constraint_violations=obj.get("constraints", 0)
        )


# =============================================================================
# AI CRITIQUE
# =============================================================================

@dataclass
class CritiqueResult:
    """Result of AI critique."""
    
    # Overall assessment
    overall_score: float  # 0-10
    summary: str
    
    # Aspect scores
    aspect_scores: Dict[str, float]  # 0-10 per aspect
    
    # Detailed feedback
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    
    # Technical issues
    critical_issues: List[str]
    warnings: List[str]
    
    # Raw response
    raw_response: str
    
    # Metadata
    model_used: str
    analysis_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "summary": self.summary,
            "aspect_scores": self.aspect_scores,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "suggestions": self.suggestions,
            "critical_issues": self.critical_issues,
            "warnings": self.warnings,
            "model_used": self.model_used,
            "analysis_time": round(self.analysis_time, 2)
        }


class AICritic:
    """
    AI-powered layout critic using local Ollama.
    
    Uses Llama 3.2 3B to analyze campus layouts and provide
    intelligent feedback and suggestions.
    
    Example:
        critic = AICritic()
        result = critic.critique(genes, polygons, metrics)
        print(result.summary)
        print(result.suggestions)
    """
    
    def __init__(self, config: CritiqueConfig = None):
        self.config = config or CritiqueConfig()
        self.analyzer = LayoutAnalyzer()
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(
                f"{self.config.ollama_host}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _build_prompt(self, metrics: LayoutMetrics) -> str:
        """Build the analysis prompt for the LLM."""
        
        prompt = f"""You are an expert urban planner and campus architect. Analyze this university campus layout and provide detailed feedback.

## LAYOUT METRICS

### Basic Statistics
- Number of buildings: {metrics.num_buildings}
- Total footprint area: {metrics.total_footprint_area:.0f} m²
- Site area: {metrics.site_area:.0f} m²
- Site coverage: {metrics.coverage_ratio*100:.1f}%

### Building Distribution
- Building types: {json.dumps(metrics.building_types)}
- Average building size: {metrics.avg_building_size:.0f} m²
- Size variance: {metrics.size_variance:.0f} m²

### Spatial Organization
- Average building separation: {metrics.avg_building_separation:.1f} m
- Minimum separation: {metrics.min_building_separation:.1f} m
- Maximum separation: {metrics.max_building_separation:.1f} m
- Compactness score: {metrics.compactness_score:.2f} (0-1, higher is better)
- Spread radius: {metrics.spread_radius:.1f} m

### Orientation
- Dominant orientation: {metrics.dominant_orientation:.1f}°
- Orientation consistency: {metrics.orientation_consistency:.2f} (0-1)

### Optimization Results
- Overlap penalty: {metrics.overlap_penalty:.2f} (0 is ideal)
- Solar penalty: {metrics.solar_penalty:.2f} (lower is better)
- Wind penalty: {metrics.wind_penalty:.2f} (lower is better)
- Constraint violations: {metrics.constraint_violations:.2f} (0 is ideal)

## YOUR TASK

Analyze this campus layout and provide:

1. **Overall Score** (0-10): Rate the overall layout quality

2. **Aspect Scores** (0-10 each):
   - Spatial Efficiency: How well is space utilized?
   - Circulation: Are pathways and connections logical?
   - Building Relationships: Do building placements make sense functionally?
   - Environmental: How well does the layout respond to sun/wind?
   - Accessibility: Is the campus walkable and accessible?
   - Aesthetics: Is the visual composition pleasing?

3. **Strengths**: List 2-3 positive aspects of this layout

4. **Weaknesses**: List 2-3 areas that need improvement

5. **Suggestions**: Provide 3-5 specific, actionable improvements

6. **Critical Issues**: List any serious problems (if any)

7. **Summary**: Write a 2-3 sentence overall assessment

Respond in this exact JSON format:
```json
{{
    "overall_score": 7.5,
    "aspect_scores": {{
        "spatial_efficiency": 8.0,
        "circulation": 7.0,
        "building_relationships": 7.5,
        "environmental": 6.5,
        "accessibility": 7.5,
        "aesthetics": 7.0
    }},
    "strengths": ["strength 1", "strength 2"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
    "critical_issues": [],
    "summary": "This is a brief overall assessment..."
}}
```

Respond ONLY with the JSON, no additional text."""

        return prompt
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with the prompt."""
        
        payload = {
            "model": self.config.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            },
            # CRITICAL: Unload model after use to free RAM
            "keep_alive": self.config.keep_alive
        }
        
        response = requests.post(
            f"{self.config.ollama_host}/api/generate",
            json=payload,
            timeout=self.config.timeout
        )
        
        if response.status_code != 200:
            raise RuntimeError(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        return result.get("response", "")
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM response into structured data."""
        
        # Try to extract JSON from response
        try:
            # Find JSON block
            start = response.find("{")
            end = response.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Fallback: return default structure
        return self._get_fallback_response()
    
    def _get_fallback_response(self) -> Dict[str, Any]:
        """Get fallback response when LLM fails."""
        return {
            "overall_score": 5.0,
            "aspect_scores": {
                "spatial_efficiency": 5.0,
                "circulation": 5.0,
                "building_relationships": 5.0,
                "environmental": 5.0,
                "accessibility": 5.0,
                "aesthetics": 5.0
            },
            "strengths": ["Layout generated successfully"],
            "weaknesses": ["AI analysis unavailable - using default assessment"],
            "suggestions": ["Consider running with Ollama for detailed analysis"],
            "critical_issues": [],
            "summary": "Basic layout generated. AI critique unavailable - please ensure Ollama is running for detailed analysis."
        }
    
    def _generate_rule_based_critique(self, metrics: LayoutMetrics) -> Dict[str, Any]:
        """Generate critique using rules when LLM is unavailable."""
        
        scores = {}
        strengths = []
        weaknesses = []
        suggestions = []
        critical = []
        
        # Spatial efficiency
        if metrics.coverage_ratio < 0.3:
            scores["spatial_efficiency"] = 6.0
            weaknesses.append("Site is underutilized - only {:.0f}% coverage".format(metrics.coverage_ratio * 100))
            suggestions.append("Consider adding more buildings to improve site utilization")
        elif metrics.coverage_ratio > 0.6:
            scores["spatial_efficiency"] = 5.0
            weaknesses.append("Site may be overcrowded - {:.0f}% coverage".format(metrics.coverage_ratio * 100))
            critical.append("Coverage exceeds recommended 60% maximum")
        else:
            scores["spatial_efficiency"] = 8.0
            strengths.append("Good site coverage ratio ({:.0f}%)".format(metrics.coverage_ratio * 100))
        
        # Circulation (based on separation)
        if metrics.min_building_separation < 6:
            scores["circulation"] = 4.0
            critical.append("Buildings too close - minimum {:.1f}m separation".format(metrics.min_building_separation))
        elif metrics.avg_building_separation < 15:
            scores["circulation"] = 6.0
            suggestions.append("Increase average building separation for better circulation")
        else:
            scores["circulation"] = 8.0
            strengths.append("Good building separation for pedestrian circulation")
        
        # Building relationships
        if metrics.compactness_score > 0.5:
            scores["building_relationships"] = 8.0
            strengths.append("Compact layout promotes interaction")
        else:
            scores["building_relationships"] = 6.0
            suggestions.append("Consider clustering related building types")
        
        # Environmental
        env_score = 7.0
        if metrics.solar_penalty > 100:
            env_score -= 2
            weaknesses.append("Significant solar shadowing issues")
        if metrics.wind_penalty > 0.5:
            env_score -= 1
            suggestions.append("Improve road alignment with prevailing winds")
        scores["environmental"] = max(3, env_score)
        
        # Accessibility
        if metrics.spread_radius > 300:
            scores["accessibility"] = 5.0
            weaknesses.append("Campus may be too spread out for walking")
        else:
            scores["accessibility"] = 7.5
        
        # Aesthetics (orientation consistency)
        if metrics.orientation_consistency > 0.7:
            scores["aesthetics"] = 8.0
            strengths.append("Consistent building orientation creates visual harmony")
        else:
            scores["aesthetics"] = 6.0
            suggestions.append("Consider aligning buildings for visual consistency")
        
        # Overall score
        overall = np.mean(list(scores.values()))
        
        # Adjust for critical issues
        if metrics.overlap_penalty > 0:
            overall -= 2
            critical.append("Building overlaps detected!")
        if metrics.constraint_violations > 0:
            overall -= 1
            critical.append("Constraint violations present")
        
        overall = max(1, min(10, overall))
        
        # Summary
        if overall >= 7:
            summary = "This is a well-designed campus layout with good spatial organization and building relationships."
        elif overall >= 5:
            summary = "This layout is functional but has room for improvement in several areas."
        else:
            summary = "This layout has significant issues that should be addressed before implementation."
        
        return {
            "overall_score": round(overall, 1),
            "aspect_scores": {k: round(v, 1) for k, v in scores.items()},
            "strengths": strengths[:3] if strengths else ["Layout generated successfully"],
            "weaknesses": weaknesses[:3] if weaknesses else ["No major weaknesses identified"],
            "suggestions": suggestions[:5] if suggestions else ["Continue refining the layout"],
            "critical_issues": critical,
            "summary": summary
        }
    
    def critique(
        self,
        genes: List[BuildingGene],
        polygons: List[Polygon],
        objective_values: Dict[str, float] = None,
        site_boundary: Polygon = None
    ) -> CritiqueResult:
        """
        Critique a campus layout.
        
        Args:
            genes: List of BuildingGene objects
            polygons: List of building polygons
            objective_values: Objective values from optimizer
            site_boundary: Site boundary polygon
            
        Returns:
            CritiqueResult object
        """
        import time
        start_time = time.time()
        
        # Set site boundary for analyzer
        if site_boundary:
            self.analyzer.site_boundary = site_boundary
        
        # Analyze layout
        metrics = self.analyzer.analyze(genes, polygons, objective_values)
        
        # Try Ollama first
        model_used = self.config.model_name
        raw_response = ""
        
        if self._check_ollama_available():
            try:
                prompt = self._build_prompt(metrics)
                raw_response = self._call_ollama(prompt)
                parsed = self._parse_response(raw_response)
            except Exception as e:
                print(f"Warning: Ollama call failed: {e}")
                if self.config.use_fallback_on_error:
                    parsed = self._generate_rule_based_critique(metrics)
                    model_used = "rule_based_fallback"
                else:
                    raise
        else:
            # Use rule-based fallback
            parsed = self._generate_rule_based_critique(metrics)
            model_used = "rule_based_fallback"
            raw_response = "Ollama not available - using rule-based analysis"
        
        elapsed = time.time() - start_time
        
        return CritiqueResult(
            overall_score=parsed.get("overall_score", 5.0),
            summary=parsed.get("summary", "Analysis complete."),
            aspect_scores=parsed.get("aspect_scores", {}),
            strengths=parsed.get("strengths", []),
            weaknesses=parsed.get("weaknesses", []),
            suggestions=parsed.get("suggestions", []),
            critical_issues=parsed.get("critical_issues", []),
            warnings=parsed.get("warnings", []),
            raw_response=raw_response,
            model_used=model_used,
            analysis_time=elapsed
        )


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def quick_critique(
    genes: List[BuildingGene],
    polygons: List[Polygon],
    objective_values: Dict[str, float] = None
) -> CritiqueResult:
    """
    Quick critique of a layout.
    
    Returns CritiqueResult with analysis.
    """
    critic = AICritic()
    return critic.critique(genes, polygons, objective_values)


def critique_solution(
    problem,  # CampusOptimizationProblem
    solution: np.ndarray
) -> CritiqueResult:
    """
    Critique a solution from the optimizer.
    
    Args:
        problem: CampusOptimizationProblem instance
        solution: Decision variable vector
        
    Returns:
        CritiqueResult
    """
    # Decode solution
    genes, polygons = problem.decode_solution(solution)
    
    # Get objective values
    details = problem.get_solution_details(solution)
    objectives = details.get("objectives", {})
    
    # Get site boundary
    boundary = problem.context.boundary if hasattr(problem, 'context') else None
    
    # Critique
    critic = AICritic()
    return critic.critique(genes, polygons, objectives, boundary)
