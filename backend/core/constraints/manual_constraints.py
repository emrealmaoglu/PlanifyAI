"""
Manual Constraints for God Mode.

Allows users to define exclusion zones, preferred areas,
and fixed building placements that the optimizer must respect.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from shapely.geometry import Polygon, Point, MultiPolygon, box
from shapely.ops import unary_union


class ConstraintType(Enum):
    """Types of manual constraints."""
    EXCLUSION = "exclusion"           # No buildings allowed
    PREFERRED = "preferred"           # Buildings encouraged here
    FIXED_BUILDING = "fixed_building" # Specific building must be here
    ROAD_ANCHOR = "road_anchor"       # Road must connect here
    GREEN_SPACE = "green_space"       # Reserved for vegetation
    PARKING = "parking"               # Parking area
    UTILITY = "utility"               # Utility infrastructure


@dataclass
class ManualConstraint:
    """A single user-defined constraint."""
    id: str
    constraint_type: ConstraintType
    geometry: Polygon                  # Shapely polygon
    properties: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1                  # Higher = more important
    
    @property
    def area(self) -> float:
        return self.geometry.area
    
    @property
    def centroid(self) -> Tuple[float, float]:
        c = self.geometry.centroid
        return (c.x, c.y)
    
    def contains_point(self, x: float, y: float) -> bool:
        """Check if point is inside this constraint."""
        return self.geometry.contains(Point(x, y))
    
    def intersects_polygon(self, other: Polygon) -> bool:
        """Check if another polygon intersects this constraint."""
        return self.geometry.intersects(other)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        from shapely.geometry import mapping
        return {
            "id": self.id,
            "type": self.constraint_type.value,
            "geometry": mapping(self.geometry),
            "properties": self.properties,
            "priority": self.priority,
            "area": self.area,
            "centroid": self.centroid
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ManualConstraint':
        """Create from dictionary."""
        from shapely.geometry import shape
        return cls(
            id=data["id"],
            constraint_type=ConstraintType(data["type"]),
            geometry=shape(data["geometry"]),
            properties=data.get("properties", {}),
            priority=data.get("priority", 1)
        )


@dataclass
class FixedBuilding:
    """A user-placed fixed building."""
    id: str
    building_type: str              # "academic", "dormitory", etc.
    position: Tuple[float, float]   # Centroid (x, y)
    width: float                    # meters
    depth: float                    # meters
    floors: int
    orientation: float = 0.0        # radians
    
    @property
    def height(self) -> float:
        return self.floors * 3.5
    
    @property
    def polygon(self) -> Polygon:
        """Generate building polygon."""
        from shapely.affinity import rotate, translate
        
        # Create rectangle at origin
        half_w = self.width / 2
        half_d = self.depth / 2
        rect = box(-half_w, -half_d, half_w, half_d)
        
        # Rotate and translate
        rotated = rotate(rect, np.degrees(self.orientation), origin=(0, 0))
        placed = translate(rotated, xoff=self.position[0], yoff=self.position[1])
        
        return placed
    
    def to_dict(self) -> Dict[str, Any]:
        from shapely.geometry import mapping
        return {
            "id": self.id,
            "building_type": self.building_type,
            "position": self.position,
            "width": self.width,
            "depth": self.depth,
            "floors": self.floors,
            "orientation": self.orientation,
            "height": self.height,
            "geometry": mapping(self.polygon)
        }


class ManualConstraintManager:
    """
    Manages all user-defined constraints for a planning session.
    
    Provides methods to:
    - Add/remove constraints
    - Check if a building placement violates constraints
    - Get buildable area after applying exclusions
    - Export/import constraints as GeoJSON
    """
    
    def __init__(self):
        self.constraints: Dict[str, ManualConstraint] = {}
        self.fixed_buildings: Dict[str, FixedBuilding] = {}
        self._exclusion_union: Optional[Polygon] = None
        self._preferred_union: Optional[Polygon] = None
    
    def add_constraint(self, constraint: ManualConstraint) -> None:
        """Add a manual constraint."""
        self.constraints[constraint.id] = constraint
        self._invalidate_cache()
    
    def remove_constraint(self, constraint_id: str) -> bool:
        """Remove a constraint by ID."""
        if constraint_id in self.constraints:
            del self.constraints[constraint_id]
            self._invalidate_cache()
            return True
        return False
    
    def add_fixed_building(self, building: FixedBuilding) -> None:
        """Add a fixed building placement."""
        self.fixed_buildings[building.id] = building
    
    def remove_fixed_building(self, building_id: str) -> bool:
        """Remove a fixed building by ID."""
        if building_id in self.fixed_buildings:
            del self.fixed_buildings[building_id]
            return True
        return False
    
    def _invalidate_cache(self) -> None:
        """Clear cached union geometries."""
        self._exclusion_union = None
        self._preferred_union = None
    
    @property
    def exclusion_zones(self) -> List[ManualConstraint]:
        """Get all exclusion-type constraints."""
        exclusion_types = {
            ConstraintType.EXCLUSION,
            ConstraintType.GREEN_SPACE,
            ConstraintType.PARKING,
            ConstraintType.UTILITY
        }
        return [c for c in self.constraints.values() 
                if c.constraint_type in exclusion_types]
    
    @property
    def preferred_zones(self) -> List[ManualConstraint]:
        """Get all preferred-type constraints."""
        return [c for c in self.constraints.values() 
                if c.constraint_type == ConstraintType.PREFERRED]
    
    def get_exclusion_union(self) -> Polygon:
        """Get union of all exclusion zones (cached)."""
        if self._exclusion_union is None:
            zones = self.exclusion_zones
            if zones:
                self._exclusion_union = unary_union([c.geometry for c in zones])
            else:
                self._exclusion_union = Polygon()  # Empty
        return self._exclusion_union
    
    def get_preferred_union(self) -> Polygon:
        """Get union of all preferred zones (cached)."""
        if self._preferred_union is None:
            zones = self.preferred_zones
            if zones:
                self._preferred_union = unary_union([c.geometry for c in zones])
            else:
                self._preferred_union = Polygon()  # Empty
        return self._preferred_union
    
    def is_position_allowed(self, x: float, y: float) -> bool:
        """Check if a point is in allowed area (not in exclusion zones)."""
        exclusion = self.get_exclusion_union()
        if exclusion.is_empty:
            return True
        return not exclusion.contains(Point(x, y))
    
    def is_polygon_allowed(self, polygon: Polygon) -> Tuple[bool, float]:
        """
        Check if a polygon placement is allowed.
        
        Returns:
            Tuple of (is_allowed, violation_area)
            - is_allowed: True if no overlap with exclusion zones
            - violation_area: Area of overlap (0 if allowed)
        """
        exclusion = self.get_exclusion_union()
        if exclusion.is_empty:
            return True, 0.0
        
        if polygon.intersects(exclusion):
            violation = polygon.intersection(exclusion)
            return False, violation.area
        
        return True, 0.0
    
    def get_preferred_bonus(self, polygon: Polygon) -> float:
        """
        Get bonus score for building in preferred zone.
        
        Returns:
            Float 0-1 representing how much of building is in preferred area
        """
        preferred = self.get_preferred_union()
        if preferred.is_empty:
            return 0.0
        
        if polygon.intersects(preferred):
            overlap = polygon.intersection(preferred)
            return overlap.area / polygon.area
        
        return 0.0
    
    def check_building_violations(
        self,
        polygons: List[Polygon]
    ) -> Tuple[float, List[Dict]]:
        """
        Check all buildings for constraint violations.
        
        Returns:
            Tuple of (total_violation_area, violation_details)
        """
        total_violation = 0.0
        details = []
        
        exclusion = self.get_exclusion_union()
        
        for i, poly in enumerate(polygons):
            allowed, violation_area = self.is_polygon_allowed(poly)
            if not allowed:
                total_violation += violation_area
                details.append({
                    "building_idx": i,
                    "violation_area": violation_area,
                    "violation_percent": violation_area / poly.area * 100
                })
        
        # Check overlap with fixed buildings
        for fixed in self.fixed_buildings.values():
            fixed_poly = fixed.polygon
            for i, poly in enumerate(polygons):
                if poly.intersects(fixed_poly):
                    overlap = poly.intersection(fixed_poly)
                    total_violation += overlap.area * 2  # Double penalty for fixed building overlap
                    details.append({
                        "building_idx": i,
                        "type": "fixed_building_overlap",
                        "fixed_building_id": fixed.id,
                        "overlap_area": overlap.area
                    })
        
        return total_violation, details
    
    def get_buildable_area(self, boundary: Polygon) -> Polygon:
        """
        Get buildable area within boundary after exclusions.
        
        Args:
            boundary: Site boundary polygon
            
        Returns:
            Polygon representing buildable area
        """
        exclusion = self.get_exclusion_union()
        
        if exclusion.is_empty:
            return boundary
        
        buildable = boundary.difference(exclusion)
        
        # Handle MultiPolygon result
        if isinstance(buildable, MultiPolygon):
            # Return largest contiguous area
            return max(buildable.geoms, key=lambda p: p.area)
        
        return buildable
    
    def to_geojson(self) -> Dict[str, Any]:
        """Export all constraints as GeoJSON FeatureCollection."""
        features = []
        
        # Constraints
        for constraint in self.constraints.values():
            from shapely.geometry import mapping
            features.append({
                "type": "Feature",
                "id": constraint.id,
                "properties": {
                    "layer": "constraint",
                    "constraint_type": constraint.constraint_type.value,
                    "priority": constraint.priority,
                    **constraint.properties
                },
                "geometry": mapping(constraint.geometry)
            })
        
        # Fixed buildings
        for building in self.fixed_buildings.values():
            features.append({
                "type": "Feature",
                "id": building.id,
                "properties": {
                    "layer": "fixed_building",
                    "building_type": building.building_type,
                    "floors": building.floors,
                    "height": building.height,
                    "width": building.width,
                    "depth": building.depth
                },
                "geometry": building.to_dict()["geometry"]
            })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    
    @classmethod
    def from_geojson(cls, geojson: Dict[str, Any]) -> 'ManualConstraintManager':
        """Import constraints from GeoJSON."""
        manager = cls()
        
        for feature in geojson.get("features", []):
            props = feature.get("properties", {})
            
            # Handle frontend God Mode constraints (MapboxDraw)
            if "user_constraint_type" in props:
                c_type = props["user_constraint_type"]
                # Map frontend types to backend types if needed
                # Currently they match: 'exclusion', 'green_space'
                
                constraint = ManualConstraint.from_dict({
                    "id": str(feature.get("id", f"constraint_{len(manager.constraints)}")),
                    "type": c_type,
                    "geometry": feature.get("geometry"),
                    "priority": props.get("priority", 1),
                    "properties": props
                })
                manager.add_constraint(constraint)
                continue

            # Handle existing backend export format
            if props.get("layer") == "constraint":
                constraint = ManualConstraint.from_dict({
                    "id": str(feature.get("id", f"constraint_{len(manager.constraints)}")),
                    "type": props.get("constraint_type", "exclusion"),
                    "geometry": feature.get("geometry"),
                    "priority": props.get("priority", 1),
                    "properties": {k: v for k, v in props.items() 
                                  if k not in ["layer", "constraint_type", "priority"]}
                })
                manager.add_constraint(constraint)
            
            elif props.get("layer") == "fixed_building":
                from shapely.geometry import shape
                geom = shape(feature.get("geometry"))
                centroid = geom.centroid
                
                building = FixedBuilding(
                    id=feature.get("id", f"fixed_{len(manager.fixed_buildings)}"),
                    building_type=props.get("building_type", "academic"),
                    position=(centroid.x, centroid.y),
                    width=props.get("width", 40),
                    depth=props.get("depth", 30),
                    floors=props.get("floors", 3),
                    orientation=props.get("orientation", 0)
                )
                manager.add_fixed_building(building)
        
        return manager


# Convenience functions
def create_exclusion_zone(
    coordinates: List[Tuple[float, float]],
    zone_type: str = "exclusion",
    name: str = None
) -> ManualConstraint:
    """Create an exclusion zone from coordinates."""
    import uuid
    
    return ManualConstraint(
        id=name or f"zone_{uuid.uuid4().hex[:8]}",
        constraint_type=ConstraintType(zone_type),
        geometry=Polygon(coordinates),
        properties={"name": name} if name else {}
    )


def create_fixed_building(
    x: float,
    y: float,
    building_type: str,
    width: float = 40,
    depth: float = 30,
    floors: int = 3,
    name: str = None
) -> FixedBuilding:
    """Create a fixed building at a location."""
    import uuid
    
    return FixedBuilding(
        id=name or f"fixed_{uuid.uuid4().hex[:8]}",
        building_type=building_type,
        position=(x, y),
        width=width,
        depth=depth,
        floors=floors
    )
