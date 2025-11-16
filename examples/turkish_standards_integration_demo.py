"""
Demonstration of Turkish Standards + H-SAGA Integration

Shows complete workflow from building definition to optimization
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.optimization import (
    BuildingTypeMapper,
    ObjectiveFunctions,
    TurkishConstraintValidator,
)
from shapely.geometry import box


def main():
    """Run integration demonstration"""

    print("=" * 60)
    print("Turkish Standards + H-SAGA Integration Demo")
    print("=" * 60)
    print()

    # 1. Define campus buildings
    print("1. Defining campus buildings...")

    class Building:
        def __init__(self, id, type, area, floors, position):
            self.id = id
            self.building_id = id
            self.type = type
            self.building_type = type
            self.area = area
            self.floors = floors
            self.position = position

    buildings = [
        Building("B001", "educational_university", 8000, 5, (50, 50)),
        Building("B002", "educational_university", 6000, 4, (150, 50)),
        Building("B003", "residential_low", 4000, 3, (50, 150)),
        Building("B004", "residential_low", 3500, 3, (150, 150)),
        Building("B005", "health_clinic", 2500, 2, (100, 100)),
        Building("B006", "commercial_office", 3000, 4, (200, 100)),
        Building("B007", "social_sports", 4000, 2, (100, 200)),
    ]

    print(f"   Created {len(buildings)} buildings")
    print()

    # 2. Map to Turkish classifications
    print("2. Mapping to Turkish building classifications...")
    mapper = BuildingTypeMapper()
    turkish_buildings = mapper.map_building_list(buildings)

    print("   Building Classifications:")
    for tb in turkish_buildings:
        print(
            f"   - {tb.building_id}: {tb.building_type} → "
            f"Class {tb.turkish_class.value} "
            f"({tb.cost_per_sqm:,.0f} TL/m²)"
        )
    print()

    # 3. Calculate costs
    print("3. Calculating construction costs (Ankara, standard quality)...")
    objectives = ObjectiveFunctions(location="ankara", quality="standard")

    total_cost = objectives.minimize_cost(buildings)
    breakdown = objectives.get_cost_breakdown(buildings)

    print(f"   Total Cost: {breakdown['total_cost_tl']:,.0f} TL")
    print("   Cost by Type:")
    for btype, cost in breakdown["by_type"].items():
        print(f"   - {btype}: {cost:,.0f} TL")
    print("   Cost by Turkish Class:")
    for bclass, cost in breakdown["by_class"].items():
        print(f"   - Class {bclass}: {cost:,.0f} TL")
    print()

    # 4. Check compliance
    print("4. Checking Turkish İmar Kanunu compliance...")
    parcel_boundary = box(0, 0, 250, 250)  # 250x250m campus
    parcel_area = 62500  # 62,500 m²

    validator = TurkishConstraintValidator(
        parcel_boundary=parcel_boundary,
        parcel_area=parcel_area,
        zone_type="educational",
        enable_compliance_checks=True,
    )

    summary = validator.validate_solution(buildings)

    print(f"   Valid Solution: {summary.is_valid}")
    print(f"   Total Violations: {summary.violation_count}")
    print(f"   Errors: {summary.severity_breakdown['error']}")
    print(f"   Warnings: {summary.severity_breakdown['warning']}")

    if summary.violations:
        print("   Violations:")
        for violation in summary.violations[:5]:  # Show first 5
            print(f"   - {violation}")
    print()

    # 5. Summary
    print("=" * 60)
    print("Integration Status: ✅ SUCCESS")
    print("=" * 60)
    print(f"Buildings Processed: {len(buildings)}")
    print(f"Total Cost: {breakdown['total_cost_tl']:,.0f} TL")
    print(f"Compliance Status: {'✅ PASS' if summary.is_valid else '⚠️  VIOLATIONS'}")
    print()

    print("Turkish Standards successfully integrated with H-SAGA!")
    print("=" * 60)


if __name__ == "__main__":
    main()
