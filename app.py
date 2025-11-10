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
from visualization.plot_utils import CampusPlotter

# Page config
st.set_page_config(
    page_title="PlanifyAI - Campus Planning Optimization",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
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

        n_buildings = st.slider(
            "Number of Buildings",
            min_value=1,
            max_value=50,
            value=10,
            help="Number of new buildings to optimize",
        )

        st.subheader("Building Types")
        col1, col2 = st.columns(2)

        with col1:
            n_residential = st.number_input(
                "Residential",
                0,
                n_buildings,
                max(0, n_buildings // 3),
                key="res",
            )
            n_educational = st.number_input(
                "Educational", 0, n_buildings, max(0, n_buildings // 3), key="edu"
            )
            n_library = st.number_input(
                "Library", 0, n_buildings, max(1, n_buildings // 10), key="lib"
            )

        with col2:
            n_administrative = st.number_input(
                "Administrative",
                0,
                n_buildings,
                max(1, n_buildings // 10),
                key="adm",
            )
            n_sports = st.number_input(
                "Sports", 0, n_buildings, max(1, n_buildings // 10), key="spt"
            )
            n_health = st.number_input(
                "Health", 0, n_buildings, max(1, n_buildings // 10), key="hlt"
            )

        # Validate total matches n_buildings
        total_specified = (
            n_residential + n_educational + n_library + n_administrative + n_sports + n_health
        )

        if total_specified != n_buildings:
            st.warning(
                f"Total specified ({total_specified}) doesn't match "
                f"target ({n_buildings}). Please adjust."
            )
            st.session_state.buildings = None
        else:
            # Generate buildings
            buildings = generate_buildings(
                n_residential,
                n_educational,
                n_library,
                n_administrative,
                n_sports,
                n_health,
            )
            st.session_state.buildings = buildings
            st.success(f"✅ {len(buildings)} buildings configured")

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
            st.info("👈 Run optimization first to see results")
        else:
            result = st.session_state.result
            campus = st.session_state.campus_data

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Final Fitness", f"{result['fitness']:.4f}")
            with col2:
                st.metric("Runtime", f"{result['statistics']['runtime']:.2f}s")
            with col3:
                st.metric("Evaluations", f"{result['statistics']['evaluations']:,}")
            with col4:
                constraint_satisfied = result.get("constraints", {}).get("satisfied", True)
                st.metric(
                    "Constraints",
                    "✅ Satisfied" if constraint_satisfied else "❌ Violated",
                )

            # Objective breakdown
            st.subheader("Objective Breakdown")
            obj = result["objectives"]
            col1, col2 = st.columns([2, 1])
            with col1:
                # Bar chart
                import pandas as pd

                df = pd.DataFrame(
                    {
                        "Objective": ["Cost", "Walking Distance", "Adjacency"],
                        "Score": [obj["cost"], obj["walking"], obj["adjacency"]],
                    }
                )
                st.bar_chart(df.set_index("Objective"))
            with col2:
                st.dataframe(df, use_container_width=True, hide_index=True)

            # Campus layout visualization
            st.subheader("Campus Layout")
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

            except Exception as e:
                st.error(f"Error generating plot: {e}")
                import traceback

                st.code(traceback.format_exc())

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
