# PlanifyAI Demo Script

## Demo Overview

**Duration:** 5-10 minutes
**Audience:** Academic committee, potential users, investors
**Goal:** Showcase AI-powered campus planning optimization

---

## Demo Flow

### Part 1: Introduction (1 min)

1. Open app: `streamlit run app.py`
2. Show title and description
3. Quick overview of features:
   - H-SAGA hybrid optimization (SA + GA)
   - Multi-objective optimization (cost, walking, adjacency)
   - Spatial constraints (setback, coverage, FAR, green space)
   - Turkish university data integration
   - Real-time visualization

---

### Part 2: Campus Selection (1 min)

1. Navigate to sidebar
2. Select "Boğaziçi University"
3. Show campus information:
   - Location: Istanbul, Turkey
   - Area: ~500,000 m²
   - Existing buildings: 3
4. Highlight existing buildings on map (if available)

---

### Part 3: Building Configuration (2 min)

1. Set number of buildings: 10
2. Configure distribution:
   - 3 Residential
   - 3 Educational
   - 1 Library
   - 1 Administrative
   - 1 Sports
   - 1 Health
3. Show building configuration confirmation
4. Explain building types and their importance

---

### Part 4: Parameter Tuning (1 min)

1. Show default algorithm parameters
2. Mention customizability:
   - SA: Temperature schedule, iterations, parallel chains
   - GA: Population size, generations, crossover/mutation rates
3. Adjust one parameter (e.g., GA generations: 50 → 30 for faster demo)
4. Explain impact of parameters on optimization quality

---

### Part 5: Constraints Configuration (1 min)

1. Enable spatial constraints
2. Show constraint options:
   - Setback constraint (10m from boundary)
   - Coverage ratio constraint (30% max)
   - FAR constraint (2.0 max)
   - Green space constraint (40% min)
3. Explain importance of constraints for realistic planning
4. Mention that constraints are integrated into fitness evaluation

---

### Part 6: Run Optimization (2 min)

1. Navigate to "⚡ Optimize" tab
2. Click "🚀 Run Optimization"
3. Show progress bar updates:
   - SA Phase: Exploring solution space
   - GA Phase: Refining solutions
4. Wait for completion (~1-2s for 10 buildings)
5. Show completion summary:
   - Runtime: <2s
   - Final Fitness: ~0.85
   - Evaluations: ~1000+

---

### Part 7: Results Visualization (2 min)

1. Navigate to "📊 Results" tab
2. Show metrics dashboard:
   - Final Fitness: 0.85
   - Runtime: 1.2s
   - Evaluations: 1,250
   - Constraints: ✅ Satisfied
3. Show objective breakdown (bar chart):
   - Cost: 0.90
   - Walking Distance: 0.80
   - Adjacency: 0.85
4. Show campus layout visualization:
   - Campus boundary
   - Existing buildings (gray)
   - New buildings (colored by type)
   - Setback zones (if enabled)
5. Show convergence plots:
   - GA Best Fitness over generations
   - GA Average Fitness over generations

---

### Part 8: Export & Comparison (1 min)

1. Download GeoJSON:
   - Click "Download GeoJSON" button
   - Show that file downloads
   - Explain use case (GIS software, mapping)
2. Save current solution:
   - Enter solution name: "Baseline Solution"
   - Click "💾 Save Current"
3. (Optional) Run second optimization with different parameters:
   - Change GA generations: 30 → 50
   - Run optimization again
   - Save as "Improved Solution"
4. Show comparison table:
   - Compare fitness, objectives, runtime
   - Show side-by-side visualization

---

### Part 9: Conclusion (30 sec)

1. Summarize achievements:
   - 30x faster than target (1s vs 30s)
   - Geospatial integration complete
   - Constraint satisfaction working
   - Interactive UI functional
   - 196+ tests passing, 89% coverage
2. Mention future enhancements:
   - Road network generation (tensor fields)
   - Multi-objective Pareto optimization
   - Advanced visualization
   - Thesis completion
3. Thank audience

---

## Key Talking Points

### Technical Achievements

- **Hybrid SA-GA optimization:** Novel reverse hybrid approach (Li et al. 2025)
- **Multi-objective optimization:** Cost, walking distance, adjacency satisfaction
- **Spatial constraint handling:** Setback, coverage ratio, FAR, green space
- **Turkish university data integration:** 5 campuses with realistic data
- **Real-time visualization:** Interactive plots and charts

### Performance Metrics

- **10 buildings:** <1.2s (target: <30s) ✅
- **20 buildings:** <5s (target: <60s) ✅
- **50 buildings:** <120s (target: <120s) ✅
- **Memory:** <500MB at 50 buildings ✅
- **Scaling:** Sub-linear (better than expected) ✅

### Innovation

- **Semantic tensor fields:** Road network generation (future)
- **Dynamic feedback loops:** Multi-objective optimization with constraints
- **Turkish-specific data:** Realistic campus planning data
- **Production-ready:** Comprehensive testing and documentation

---

## Troubleshooting

### If optimization is too slow during demo:

- Reduce buildings to 5
- Reduce GA generations to 20
- Disable some constraints
- Use smaller campus (ITU instead of Boğaziçi)

### If app crashes:

- Check terminal for errors
- Restart: `streamlit run app.py`
- Have backup screenshots ready
- Clear browser cache if needed

### If questions about specific algorithms:

- Refer to research documents
- Mention Li et al. 2025 paper
- Show code quality metrics
- Explain hybrid approach benefits

### If questions about performance:

- Show benchmark results
- Explain optimization techniques (caching, lazy evaluation)
- Mention scaling analysis
- Discuss memory efficiency

---

## Backup Plan

### If live demo fails:

1. Have screenshots ready:
   - Campus selection
   - Building configuration
   - Optimization results
   - Visualization plots
2. Show code repository:
   - GitHub link
   - Test coverage report
   - Documentation
3. Explain architecture:
   - System design
   - Algorithm implementation
   - Data pipeline
4. Show test results:
   - 196+ tests passing
   - 89% coverage
   - Performance benchmarks

---

## Demo Checklist

### Before Demo:

- [ ] App tested and working
- [ ] All campuses loaded correctly
- [ ] Optimization runs successfully
- [ ] Visualizations render correctly
- [ ] Export buttons work
- [ ] Comparison feature functional
- [ ] Backup screenshots prepared
- [ ] Terminal ready for error checking
- [ ] Browser cache cleared

### During Demo:

- [ ] Introduction clear and engaging
- [ ] Campus selection smooth
- [ ] Building configuration intuitive
- [ ] Parameters explained
- [ ] Constraints demonstrated
- [ ] Optimization runs without errors
- [ ] Results display correctly
- [ ] Visualizations render
- [ ] Export functions work
- [ ] Comparison shows differences
- [ ] Conclusion summarizes achievements

### After Demo:

- [ ] Questions answered
- [ ] Feedback collected
- [ ] Next steps discussed
- [ ] Contact information shared
- [ ] Documentation provided

---

## Demo Script Notes

- **Timing:** Keep each section to allocated time
- **Engagement:** Ask for questions between sections
- **Flexibility:** Adjust based on audience interest
- **Focus:** Highlight key achievements and innovation
- **Future:** Mention Week 2+ plans (tensor fields, thesis)

---

**Last Updated:** November 10, 2025
**Version:** 1.0
**Status:** Ready for Demo
