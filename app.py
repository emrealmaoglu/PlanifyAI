"""
PlanifyAI - Streamlit Web Application
=====================================

AI-Powered Campus Planning Optimization Platform

Created: 2025-11-10
"""

import sys
from pathlib import Path

import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from streamlit_folium import st_folium

from algorithms.building import Building, BuildingType
from algorithms.hsaga import HybridSAGA
from constraints.spatial_constraints import (
    ConstraintManager,
    CoverageRatioConstraint,
    FloorAreaRatioConstraint,
    GreenSpaceConstraint,
    SetbackConstraint,
)
from data.export import ResultExporter
from data.parser import CampusDataParser
from visualization.interactive_map import InteractiveCampusMap
from visualization.plot_utils import CampusPlotter

# Page config
st.set_page_config(
    page_title="PlanifyAI - Campus Planning Optimization",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Headers */
    h1 {
        color: #1976D2;
        font-weight: 700;
    }

    h2 {
        color: #424242;
        font-weight: 600;
        margin-top: 1.5rem;
    }

    h3 {
        color: #616161;
        font-weight: 500;
    }

    /* Sidebar */
    .css-1d391kg {
        background-color: #FAFAFA;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 600;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }

    /* Progress bars */
    .stProgress > div > div {
        border-radius: 10px;
    }

    /* Cards */
    .stAlert {
        border-radius: 8px;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        font-weight: 500;
        font-size: 18px;
    }

    /* Tables */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .main > div {
        animation: fadeIn 0.5s ease-out;
    }
</style>
""",
    unsafe_allow_html=True,
)


def generate_buildings(n_res, n_edu, n_lib, n_adm, n_spt, n_hlt):
    """Generate building list from type counts."""
    import numpy as np

    buildings = []
    types_counts = [
        (BuildingType.RESIDENTIAL, n_res),
        (BuildingType.EDUCATIONAL, n_edu),
        (BuildingType.LIBRARY, n_lib),
        (BuildingType.ADMINISTRATIVE, n_adm),
        (BuildingType.SPORTS, n_spt),
        (BuildingType.HEALTH, n_hlt),
    ]

    idx = 0
    for btype, count in types_counts:
        for _ in range(count):
            # Realistic area and floors for each type
            area = np.random.uniform(1500, 4000)
            floors = np.random.randint(2, 6)
            buildings.append(Building(f"B{idx:02d}", btype, area, floors))
            idx += 1

    return buildings


def generate_buildings_with_names(n_res, n_edu, n_lib, n_adm, n_spt, n_hlt):
    """Generate buildings with semantic names"""
    import numpy as np

    buildings = []

    # Type configurations: (type, count, base_name)
    configs = [
        (BuildingType.RESIDENTIAL, n_res, "RES"),
        (BuildingType.EDUCATIONAL, n_edu, "EDU"),
        (BuildingType.LIBRARY, n_lib, "LIB"),
        (BuildingType.ADMINISTRATIVE, n_adm, "ADM"),
        (BuildingType.SPORTS, n_spt, "SPT"),
        (BuildingType.HEALTH, n_hlt, "HLT"),
    ]

    for btype, count, prefix in configs:
        for i in range(count):
            # Realistic area and floors for each type
            if btype == BuildingType.RESIDENTIAL:
                area = np.random.uniform(2500, 4000)
                floors = np.random.randint(4, 8)
            elif btype == BuildingType.EDUCATIONAL:
                area = np.random.uniform(2000, 3500)
                floors = np.random.randint(3, 6)
            elif btype == BuildingType.LIBRARY:
                area = np.random.uniform(2500, 4500)
                floors = np.random.randint(3, 5)
            elif btype == BuildingType.ADMINISTRATIVE:
                area = np.random.uniform(1500, 2500)
                floors = np.random.randint(2, 4)
            elif btype == BuildingType.SPORTS:
                area = np.random.uniform(3000, 5000)
                floors = np.random.randint(1, 3)
            else:  # HEALTH
                area = np.random.uniform(1800, 3000)
                floors = np.random.randint(2, 4)

            # Semantic ID: RES-01, EDU-02, etc.
            building_id = f"{prefix}-{i+1:02d}"
            buildings.append(Building(building_id, btype, area, floors))

    return buildings


def main():
    """Main application entry point."""
    st.title("🏛️ PlanifyAI - AI-Powered Campus Planning")
    st.markdown("### Generative Spatial Optimization for University Campuses")

    # Initialize session state
    if "campus_data" not in st.session_state:
        st.session_state.campus_data = None
    if "buildings" not in st.session_state:
        st.session_state.buildings = None
    if "config" not in st.session_state:
        st.session_state.config = None
    if "constraints" not in st.session_state:
        st.session_state.constraints = None
    if "optimization_run" not in st.session_state:
        st.session_state.optimization_run = False
    if "result" not in st.session_state:
        st.session_state.result = None
    if "solution_history" not in st.session_state:
        st.session_state.solution_history = []

    # Sidebar: Configuration
    with st.sidebar:
        st.header("📍 Campus Selection")

        # List available campuses
        campus_dir = Path("data/campuses")
        if campus_dir.exists():
            campus_files = list(campus_dir.glob("*.json"))
            campus_names = [f.stem.replace("_", " ").title() for f in campus_files]

            if campus_names:
                selected_campus = st.selectbox(
                    "Select Campus",
                    options=campus_names,
                    index=0,
                    help="Choose a Turkish university campus",
                )

                # Load campus data
                if selected_campus:
                    campus_file = next(
                        f
                        for f in campus_files
                        if f.stem.replace("_", " ").title() == selected_campus
                    )
                    try:
                        campus_data = CampusDataParser.from_geojson(str(campus_file))

                        # Display campus info
                        st.info(
                            f"""
                        **Location:** {campus_data.location}
                        **Area:** {campus_data.metadata.get('total_area_m2', 0):,.0f} m²
                        **Existing Buildings:** {len(campus_data.buildings)}
                        """
                        )

                        # Store in session state
                        st.session_state.campus_data = campus_data
                    except Exception as e:
                        st.error(f"Error loading campus: {e}")
            else:
                st.warning("No campus files found in data/campuses/")
        else:
            st.warning("Campus data directory not found")

        st.divider()

        # Building Configuration
        st.header("🏢 Building Configuration")

        # Use expander for cleaner look
        with st.expander("📊 Building Type Distribution", expanded=True):
            # Number of buildings
            n_buildings = st.slider(
                "Total Number of Buildings",
                min_value=5,
                max_value=50,
                value=10,
                step=1,
                help="Total buildings to place on campus",
            )

            st.markdown("---")
            st.subheader("Building Type Breakdown")

            # Quick presets
            preset = st.selectbox(
                "Quick Preset",
                ["Custom", "Balanced", "Residential Focus", "Academic Focus", "Mixed Use"],
                help="Pre-configured building distributions",
            )

            # Apply preset
            if preset == "Balanced":
                n_residential = n_buildings // 3
                n_educational = n_buildings // 3
                n_library = max(1, n_buildings // 10)
                n_administrative = max(1, n_buildings // 10)
                n_sports = max(1, n_buildings // 10)
                n_health = n_buildings - (
                    n_residential + n_educational + n_library + n_administrative + n_sports
                )
            elif preset == "Residential Focus":
                n_residential = int(n_buildings * 0.5)
                n_educational = int(n_buildings * 0.2)
                n_library = max(1, n_buildings // 15)
                n_administrative = max(1, n_buildings // 15)
                n_sports = max(1, n_buildings // 10)
                n_health = n_buildings - (
                    n_residential + n_educational + n_library + n_administrative + n_sports
                )
            elif preset == "Academic Focus":
                n_residential = int(n_buildings * 0.3)
                n_educational = int(n_buildings * 0.4)
                n_library = max(2, n_buildings // 8)
                n_administrative = max(1, n_buildings // 10)
                n_sports = max(1, n_buildings // 15)
                n_health = n_buildings - (
                    n_residential + n_educational + n_library + n_administrative + n_sports
                )
            elif preset == "Mixed Use":
                n_residential = int(n_buildings * 0.25)
                n_educational = int(n_buildings * 0.25)
                n_library = max(1, n_buildings // 10)
                n_administrative = max(1, n_buildings // 10)
                n_sports = max(2, n_buildings // 8)
                n_health = n_buildings - (
                    n_residential + n_educational + n_library + n_administrative + n_sports
                )
            else:  # Custom
                # Use session state to preserve values
                if "building_counts" not in st.session_state:
                    st.session_state.building_counts = {
                        "residential": n_buildings // 3,
                        "educational": n_buildings // 3,
                        "library": max(1, n_buildings // 10),
                        "administrative": max(1, n_buildings // 10),
                        "sports": max(1, n_buildings // 10),
                        "health": 1,
                    }

            # Building type inputs (two columns for cleaner layout)
            col1, col2 = st.columns(2)

            with col1:
                n_residential = st.number_input(
                    "🏠 Residential Halls",
                    0,
                    n_buildings,
                    value=n_residential
                    if preset != "Custom"
                    else st.session_state.building_counts["residential"],
                    help="Student dormitories and housing",
                    key="res",
                )
                n_educational = st.number_input(
                    "🎓 Academic Buildings",
                    0,
                    n_buildings,
                    value=n_educational
                    if preset != "Custom"
                    else st.session_state.building_counts["educational"],
                    help="Classrooms, lecture halls, labs",
                    key="edu",
                )
                n_library = st.number_input(
                    "📚 Libraries",
                    0,
                    n_buildings,
                    value=n_library
                    if preset != "Custom"
                    else st.session_state.building_counts["library"],
                    help="Libraries and study spaces",
                    key="lib",
                )

            with col2:
                n_administrative = st.number_input(
                    "🏛️ Administrative",
                    0,
                    n_buildings,
                    value=n_administrative
                    if preset != "Custom"
                    else st.session_state.building_counts["administrative"],
                    help="Administration and offices",
                    key="adm",
                )
                n_sports = st.number_input(
                    "⚽ Sports Facilities",
                    0,
                    n_buildings,
                    value=n_sports
                    if preset != "Custom"
                    else st.session_state.building_counts["sports"],
                    help="Gyms, sports complexes",
                    key="spt",
                )
                n_health = st.number_input(
                    "🏥 Health Centers",
                    0,
                    n_buildings,
                    value=n_health
                    if preset != "Custom"
                    else st.session_state.building_counts["health"],
                    help="Medical facilities and health services",
                    key="hlt",
                )

            # Update session state for custom
            if preset == "Custom":
                st.session_state.building_counts = {
                    "residential": n_residential,
                    "educational": n_educational,
                    "library": n_library,
                    "administrative": n_administrative,
                    "sports": n_sports,
                    "health": n_health,
                }

            # Validation
            total_specified = (
                n_residential + n_educational + n_library + n_administrative + n_sports + n_health
            )

            if total_specified != n_buildings:
                st.error(
                    f"⚠️ Total specified ({total_specified}) doesn't match "
                    f"target ({n_buildings}). Please adjust."
                )
                st.session_state.buildings = None
            else:
                # Generate buildings with semantic names
                buildings = generate_buildings_with_names(
                    n_residential, n_educational, n_library, n_administrative, n_sports, n_health
                )
                st.session_state.buildings = buildings

                # Success message with breakdown
                st.success(
                    f"""
                ✅ **{len(buildings)} buildings configured:**

                - 🏠 {n_residential} Residential
                - 🎓 {n_educational} Academic
                - 📚 {n_library} Library
                - 🏛️ {n_administrative} Administrative
                - ⚽ {n_sports} Sports
                - 🏥 {n_health} Health
                """
                )

        st.divider()

        # Algorithm Parameters
        st.header("⚙️ Algorithm Parameters")

        with st.expander("Simulated Annealing (SA)", expanded=False):
            sa_initial_temp = st.number_input(
                "Initial Temperature", 100.0, 10000.0, 1000.0, 100.0, key="sa_init"
            )
            sa_final_temp = st.number_input(
                "Final Temperature", 0.01, 10.0, 0.1, 0.01, key="sa_final"
            )
            sa_cooling_rate = st.slider("Cooling Rate", 0.80, 0.99, 0.95, 0.01, key="sa_cool")
            sa_iterations = st.number_input("Chain Iterations", 1, 100, 15, 1, key="sa_iter")
            sa_chains = st.number_input("Parallel Chains", 1, 8, 4, 1, key="sa_chains")

        with st.expander("Genetic Algorithm (GA)", expanded=False):
            ga_population = st.number_input("Population Size", 10, 200, 50, 10, key="ga_pop")
            ga_generations = st.number_input("Generations", 10, 200, 50, 10, key="ga_gen")
            ga_crossover_rate = st.slider("Crossover Rate", 0.5, 1.0, 0.8, 0.05, key="ga_cross")
            ga_mutation_rate = st.slider("Mutation Rate", 0.05, 0.5, 0.15, 0.05, key="ga_mut")
            ga_elite_size = st.number_input("Elite Size", 1, 20, 5, 1, key="ga_elite")
            ga_tournament_size = st.number_input("Tournament Size", 2, 10, 3, 1, key="ga_tour")

        # Store config in session state
        st.session_state.config = {
            "sa": {
                "initial_temp": sa_initial_temp,
                "final_temp": sa_final_temp,
                "cooling_rate": sa_cooling_rate,
                "chain_iterations": int(sa_iterations),
                "num_chains": int(sa_chains),
                "max_iterations": int(sa_iterations),
            },
            "ga": {
                "population_size": int(ga_population),
                "generations": int(ga_generations),
                "crossover_rate": ga_crossover_rate,
                "mutation_rate": ga_mutation_rate,
                "elite_size": int(ga_elite_size),
                "tournament_size": int(ga_tournament_size),
            },
        }

        st.divider()

        # Constraints Configuration
        st.header("🚧 Spatial Constraints")

        enable_constraints = st.checkbox("Enable Spatial Constraints", value=True)

        if enable_constraints and st.session_state.campus_data:
            campus = st.session_state.campus_data

            st.subheader("Constraint Configuration")

            # Setback constraint
            use_setback = st.checkbox("Setback from Boundary", value=True)
            setback_dist = 10.0
            if use_setback:
                setback_dist = st.slider(
                    "Setback Distance (m)",
                    0.0,
                    50.0,
                    float(campus.constraints.get("setback_from_boundary", 10.0)),
                    1.0,
                )

            # Coverage ratio constraint
            use_coverage = st.checkbox("Maximum Coverage Ratio", value=True)
            max_coverage = 0.3
            if use_coverage:
                max_coverage = st.slider(
                    "Max Coverage Ratio",
                    0.1,
                    0.8,
                    float(campus.constraints.get("coverage_ratio_max", 0.3)),
                    0.05,
                )

            # FAR constraint
            use_far = st.checkbox("Floor Area Ratio (FAR)", value=True)
            max_far = 2.0
            if use_far:
                max_far = st.slider(
                    "Max FAR",
                    0.5,
                    5.0,
                    float(campus.constraints.get("far_max", 2.0)),
                    0.1,
                )

            # Green space constraint
            use_green = st.checkbox("Minimum Green Space", value=True)
            min_green = 0.4
            if use_green:
                min_green = st.slider(
                    "Min Green Space Ratio",
                    0.1,
                    0.8,
                    float(campus.constraints.get("min_green_space_ratio", 0.4)),
                    0.05,
                )

            # Create constraint manager
            constraint_manager = ConstraintManager()
            if use_setback:
                constraint_manager.add_constraint(SetbackConstraint(setback_dist))
            if use_coverage:
                constraint_manager.add_constraint(CoverageRatioConstraint(max_coverage))
            if use_far:
                constraint_manager.add_constraint(FloorAreaRatioConstraint(max_far))
            if use_green:
                constraint_manager.add_constraint(GreenSpaceConstraint(min_green))

            st.session_state.constraints = constraint_manager
            st.success(f"✅ {len(constraint_manager.constraints)} constraints configured")
        else:
            st.session_state.constraints = None

    # Main area: Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🎯 Setup", "⚡ Optimize", "📊 Results", "🔄 Compare"])

    # Setup Tab
    with tab1:
        st.header("🎯 Setup & Configuration")

        # Check prerequisites
        ready = all(
            [
                st.session_state.campus_data is not None,
                st.session_state.buildings is not None,
                st.session_state.config is not None,
            ]
        )

        if not ready:
            st.warning("⚠️ Please configure campus, buildings, and parameters in the sidebar.")
        else:
            st.success("✅ All prerequisites configured! Ready to optimize.")

            # Display configuration summary
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Campus Information")
                campus = st.session_state.campus_data
                st.write(f"**Name:** {campus.name}")
                st.write(f"**Location:** {campus.location}")
                st.write(f"**Area:** {campus.metadata.get('total_area_m2', 0):,.0f} m²")
                st.write(f"**Existing Buildings:** {len(campus.buildings)}")

            with col2:
                st.subheader("Building Configuration")
                buildings = st.session_state.buildings
                st.write(f"**Total Buildings:** {len(buildings)}")
                type_counts = {}
                for b in buildings:
                    type_counts[b.type.value] = type_counts.get(b.type.value, 0) + 1
                for btype, count in type_counts.items():
                    st.write(f"**{btype.title()}:** {count}")

            # Show algorithm config
            st.subheader("Algorithm Configuration")
            config = st.session_state.config
            st.json(config)

            # Show constraints
            if st.session_state.constraints:
                st.subheader("Spatial Constraints")
                st.write(f"**Active Constraints:** {len(st.session_state.constraints.constraints)}")

    # Optimization Tab
    with tab2:
        st.header("⚡ Run Optimization")

        # Check prerequisites
        ready = all(
            [
                st.session_state.campus_data is not None,
                st.session_state.buildings is not None,
                st.session_state.config is not None,
            ]
        )

        if not ready:
            st.warning("⚠️ Please configure campus, buildings, and parameters first.")
        else:
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                run_button = st.button(
                    "🚀 Run Optimization", type="primary", use_container_width=True
                )
            with col2:
                seed = st.number_input("Random Seed", 0, 9999, 42, 1)
            with col3:
                st.checkbox("Parallel SA", value=True, disabled=True)

            if run_button:
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()

                # Create optimizer
                campus = st.session_state.campus_data
                buildings = st.session_state.buildings
                config = st.session_state.config
                constraints = st.session_state.get("constraints", None)

                # Set random seed
                import numpy as np

                np.random.seed(seed)

                try:
                    status_text.text("🔥 Initializing Simulated Annealing...")
                    progress_bar.progress(0.1)

                    optimizer = HybridSAGA(
                        buildings=buildings,
                        bounds=campus.get_bounds(),
                        campus_data=campus,
                        constraint_manager=constraints,
                        sa_config=config["sa"],
                        ga_config=config["ga"],
                    )

                    status_text.text("🔄 SA Phase: Exploring solution space...")
                    progress_bar.progress(0.3)

                    # Run actual optimization
                    result = optimizer.optimize()

                    status_text.text("🧬 GA Phase: Refining solutions...")
                    progress_bar.progress(0.8)

                    progress_bar.progress(1.0)
                    status_text.text("✅ Optimization Complete!")

                    # Store result
                    st.session_state.result = result
                    st.session_state.optimization_run = True

                    # Show summary
                    st.success(
                        f"""
                    **Optimization Complete!**

                    - Runtime: {result['statistics']['runtime']:.2f}s
                    - Final Fitness: {result['fitness']:.4f}
                    - Evaluations: {result['statistics']['evaluations']:,}
                    """
                    )

                    # Automatic switch to Results tab
                    st.rerun()

                except Exception as e:
                    st.error(f"Error during optimization: {e}")
                    import traceback

                    st.code(traceback.format_exc())

    # Results Tab
    with tab3:
        st.header("📊 Optimization Results")

        if not st.session_state.get("optimization_run", False):
            st.info("👈 Configure campus and buildings, then run optimization to see results")
        else:
            result = st.session_state.result
            campus = st.session_state.campus_data

            # Enhanced metrics with progress bars
            st.subheader("Performance Metrics")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                fitness = result["fitness"]
                st.metric("Overall Fitness", f"{fitness:.2%}")
                st.progress(fitness)

            with col2:
                runtime = result["statistics"]["runtime"]
                target_time = 30.0  # Target: <30s
                status = "✅" if runtime < target_time else "⚠️"
                st.metric("Runtime", f"{runtime:.2f}s", delta=f"{status}")
                st.caption(f"Target: <{target_time}s")

            with col3:
                evals = result["statistics"]["evaluations"]
                st.metric("Evaluations", f"{evals:,}")
                st.caption(f"{evals/runtime:.0f} evals/sec")

            with col4:
                constraint_satisfied = result.get("constraints", {}).get("satisfied", True)
                constraint_penalty = result.get("constraints", {}).get("penalty", 0.0)

                if constraint_satisfied:
                    st.metric("Constraints", "✅ Satisfied")
                    st.success("All spatial constraints met")
                else:
                    st.metric("Constraints", "❌ Violated")
                    st.error(f"Penalty: {constraint_penalty:.2%}")

            # Road network statistics
            if "road_stats" in result and result["road_stats"]:
                st.subheader("🛣️ Road Network")
                road_stats = result["road_stats"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Major Roads", road_stats.get("n_major_roads", 0))
                with col2:
                    st.metric("Minor Roads", road_stats.get("n_minor_roads", 0))
                with col3:
                    st.metric(
                        "Total Length",
                        f"{road_stats.get('total_length_m', 0):.0f}m",
                    )

            # Objective breakdown with detailed cards
            st.subheader("🎯 Objective Scores")
            obj = result["objectives"]

            col1, col2, col3 = st.columns(3)

            with col1:
                cost_score = obj["cost"]
                st.markdown(
                    f"""
                <div style='background-color: #E3F2FD; padding: 20px;
                    border-radius: 10px; border-left: 5px solid #1976D2;'>
                    <h4 style='margin: 0; color: #1976D2;'>💰 Construction Cost</h4>
                    <h2 style='margin: 10px 0; color: #1565C0;'>{cost_score:.1%}</h2>
                    <p style='margin: 0; color: #424242; font-size: 14px;'>
                        Lower construction and operational costs
                    </p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                st.progress(cost_score)

            with col2:
                walking_score = obj["walking"]
                st.markdown(
                    f"""
                <div style='background-color: #E8F5E9; padding: 20px;
                    border-radius: 10px; border-left: 5px solid #388E3C;'>
                    <h4 style='margin: 0; color: #388E3C;'>🚶 Walking Distance</h4>
                    <h2 style='margin: 10px 0; color: #2E7D32;'>{walking_score:.1%}</h2>
                    <p style='margin: 0; color: #424242; font-size: 14px;'>
                        Shorter distances between buildings
                    </p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                st.progress(walking_score)

            with col3:
                adjacency_score = obj["adjacency"]
                st.markdown(
                    f"""
                <div style='background-color: #F3E5F5; padding: 20px;
                    border-radius: 10px; border-left: 5px solid #7B1FA2;'>
                    <h4 style='margin: 0; color: #7B1FA2;'>🔗 Adjacency</h4>
                    <h2 style='margin: 10px 0; color: #6A1B9A;'>{adjacency_score:.1%}</h2>
                    <p style='margin: 0; color: #424242; font-size: 14px;'>
                        Compatible building types nearby
                    </p>
                </div>
                """,
                    unsafe_allow_html=True,
                )
                st.progress(adjacency_score)

            # INTERACTIVE MAP (NEW!)
            st.subheader("🗺️ Interactive Campus Layout")

            # Map view options
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.info("🔍 Use mouse to pan and zoom. Click buildings for details.")
            with col2:
                map_style = st.selectbox(
                    "Map Style",
                    ["OpenStreetMap", "CartoDB Positron", "CartoDB Dark Matter"],
                    index=0,
                )
            with col3:
                show_boundary = st.checkbox("Show Campus Boundary", value=True)

            # Get buildings from session state
            buildings = st.session_state.buildings

            # Create interactive map
            try:
                # Map tile style
                tile_style = "OpenStreetMap"
                if map_style == "CartoDB Positron":
                    tile_style = "CartoDB positron"
                elif map_style == "CartoDB Dark Matter":
                    tile_style = "CartoDB dark_matter"

                mapper = InteractiveCampusMap(
                    campus_data=campus, buildings=buildings, show_boundary=show_boundary
                )
                folium_map = mapper.create_map(
                    result["best_solution"],
                    buildings=buildings,
                    tiles=tile_style,
                    major_roads=result.get("major_roads"),
                    minor_roads=result.get("minor_roads"),
                )

                # Display map (full width)
                st_folium(
                    folium_map,
                    width=None,  # Full width
                    height=600,
                    returned_objects=[],  # Don't need click events for now
                )

                # Building details table
                st.subheader("📋 Building Details")
                building_data = []
                for building_id, position in result["best_solution"].positions.items():
                    building = next((b for b in buildings if b.id == building_id), None)
                    if not building:
                        continue

                    # Use semantic name
                    building_dict = {b.id: b for b in buildings}
                    name = mapper._get_building_name(building, building_dict)

                    building_data.append(
                        {
                            "Name": name,
                            "Type": building.type.name.title(),
                            "Area (m²)": f"{building.area:,.0f}",
                            "Floors": building.floors,
                            "Total Floor Area (m²)": f"{building.area * building.floors:,.0f}",
                            "Position X": f"{position[0]:.1f}",
                            "Position Y": f"{position[1]:.1f}",
                        }
                    )

                if building_data:
                    import pandas as pd

                    df_buildings = pd.DataFrame(building_data)
                    st.dataframe(df_buildings, use_container_width=True, hide_index=True)

            except Exception as e:
                st.error(f"Error generating interactive map: {e}")
                import traceback

                st.code(traceback.format_exc())

                # Fallback to static plot
                st.warning("Falling back to static plot...")
                try:
                    plotter = CampusPlotter(campus)
                    import tempfile
                    from pathlib import Path as PathLib

                    temp_dir = PathLib(tempfile.gettempdir())
                    plot_path = temp_dir / "campus_plot.png"

                    plotter.plot_solution(
                        result["best_solution"],
                        show_constraints=True,
                        save_path=str(plot_path),
                        buildings=buildings,
                    )

                    st.image(str(plot_path))
                except Exception as e2:
                    st.error(f"Error generating fallback plot: {e2}")

            # Convergence plot
            st.subheader("Convergence History")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**GA Best Fitness**")
                ga_best = result["convergence"].get("ga_best_history", [])
                if ga_best:
                    st.line_chart(ga_best)
                else:
                    st.info("No convergence data available")
            with col2:
                st.write("**GA Average Fitness**")
                ga_avg = result["convergence"].get("ga_avg_history", [])
                if ga_avg:
                    st.line_chart(ga_avg)
                else:
                    st.info("No convergence data available")

            # Constraint violations (if any)
            if "constraints" in result:
                violations = result["constraints"].get("violations", {})
                if violations:
                    st.warning("⚠️ Constraint Violations Detected")
                    for constraint, penalty in violations.items():
                        st.error(f"- {constraint}: Penalty = {penalty:.4f}")

            # Export section
            st.subheader("📥 Export Results")
            col1, col2, col3 = st.columns(3)

            try:
                with col1:
                    # Export GeoJSON
                    geojson_data = ResultExporter.to_geojson_dict(
                        result["best_solution"], campus, buildings
                    )
                    import json

                    st.download_button(
                        "Download GeoJSON",
                        data=json.dumps(geojson_data, indent=2),
                        file_name="campus_solution.geojson",
                        mime="application/json",
                    )

                with col2:
                    # Export CSV
                    csv_data = ResultExporter.to_csv_string(result["best_solution"], buildings)
                    st.download_button(
                        "Download CSV",
                        data=csv_data,
                        file_name="building_positions.csv",
                        mime="text/csv",
                    )

                with col3:
                    # Export Report
                    report_data = ResultExporter.generate_report_string(result)
                    st.download_button(
                        "Download Report",
                        data=report_data,
                        file_name="optimization_report.md",
                        mime="text/markdown",
                    )
            except Exception as e:
                st.error(f"Error preparing exports: {e}")

    # Comparison Tab
    with tab4:
        st.header("🔄 Compare Solutions")

        st.info("Run optimization multiple times with different parameters to compare solutions")

        # Solution history management
        if "solution_history" not in st.session_state:
            st.session_state.solution_history = []

        # Add current result to history
        col1, col2 = st.columns([3, 1])
        with col1:
            solution_name = st.text_input(
                "Solution Name",
                f"Solution_{len(st.session_state.solution_history)+1}",
            )
        with col2:
            if st.button("💾 Save Current", use_container_width=True):
                if st.session_state.get("optimization_run", False):
                    st.session_state.solution_history.append(
                        {
                            "name": solution_name,
                            "result": st.session_state.result,
                            "config": st.session_state.config.copy(),
                            "campus": st.session_state.campus_data.name,
                        }
                    )
                    st.success(f"✅ Saved as '{solution_name}'")
                    st.rerun()

        # Display comparison table
        if st.session_state.solution_history:
            st.subheader(f"Saved Solutions ({len(st.session_state.solution_history)})")

            # Create comparison dataframe
            comparison_data = []
            for i, sol in enumerate(st.session_state.solution_history):
                result = sol["result"]
                comparison_data.append(
                    {
                        "Name": sol["name"],
                        "Campus": sol["campus"],
                        "Fitness": f"{result['fitness']:.4f}",
                        "Cost": f"{result['objectives']['cost']:.4f}",
                        "Walking": f"{result['objectives']['walking']:.4f}",
                        "Adjacency": f"{result['objectives']['adjacency']:.4f}",
                        "Runtime": f"{result['statistics']['runtime']:.2f}s",
                        "Constraints": "✅"
                        if result.get("constraints", {}).get("satisfied", True)
                        else "❌",
                    }
                )

            df = pd.DataFrame(comparison_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Side-by-side visualization
            if len(st.session_state.solution_history) >= 2:
                st.subheader("Side-by-Side Comparison")

                sol_indices = st.multiselect(
                    "Select 2 solutions to compare",
                    options=list(range(len(st.session_state.solution_history))),
                    default=[0, min(1, len(st.session_state.solution_history) - 1)],
                    format_func=lambda x: st.session_state.solution_history[x]["name"],
                    max_selections=2,
                )

                if len(sol_indices) == 2:
                    col1, col2 = st.columns(2)

                    sol1 = st.session_state.solution_history[sol_indices[0]]
                    sol2 = st.session_state.solution_history[sol_indices[1]]

                    with col1:
                        st.write(f"**{sol1['name']}**")
                        st.metric("Fitness", f"{sol1['result']['fitness']:.4f}")
                        # Plot solution 1
                        try:
                            import tempfile
                            from pathlib import Path as PathLib

                            temp_dir = PathLib(tempfile.gettempdir())
                            plotter = CampusPlotter(st.session_state.campus_data)
                            plot_path1 = temp_dir / "solution1_plot.png"
                            plotter.plot_solution(
                                sol1["result"]["best_solution"],
                                save_path=str(plot_path1),
                                buildings=st.session_state.buildings,
                            )
                            st.image(str(plot_path1))
                        except Exception as e:
                            st.error(f"Error plotting: {e}")

                    with col2:
                        st.write(f"**{sol2['name']}**")
                        st.metric("Fitness", f"{sol2['result']['fitness']:.4f}")
                        # Plot solution 2
                        try:
                            import tempfile
                            from pathlib import Path as PathLib

                            temp_dir = PathLib(tempfile.gettempdir())
                            plotter = CampusPlotter(st.session_state.campus_data)
                            plot_path2 = temp_dir / "solution2_plot.png"
                            plotter.plot_solution(
                                sol2["result"]["best_solution"],
                                save_path=str(plot_path2),
                                buildings=st.session_state.buildings,
                            )
                            st.image(str(plot_path2))
                        except Exception as e:
                            st.error(f"Error plotting: {e}")

            # Clear history button
            if st.button("🗑️ Clear History", type="secondary"):
                st.session_state.solution_history = []
                st.rerun()


if __name__ == "__main__":
    main()
