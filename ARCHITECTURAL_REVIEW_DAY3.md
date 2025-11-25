# Architectural Review Report: Streamline Integration

## 1. Integration Method
**Recommended Method:** `scipy.integrate.RK45` (Direct class usage)
**Rationale:**
*   **Adaptivity:** Essential for handling varying curvature (straight grids vs. tight radial turns).
*   **Control:** Using the class directly (instead of `solve_ivp`) allows step-by-step iteration, which is critical for checking custom termination conditions (boundaries, singularities) *during* integration.
*   **Performance:** Efficient enough for Python. The overhead is in the Python loop, but for road generation (hundreds of roads, not millions), it's acceptable on M1.

**Parameters:**
*   `max_step`: **5.0 meters** (10.0m might be too coarse for tight junctions).
*   `rtol`: `1e-3` (Standard).
*   `atol`: `1e-6` (Standard).

## 2. Termination Logic
**Verdict:** 🔴 **FLAWED (Critical Issue Identified)**

**Critical Fixes:**
1.  **Singularity Detection:** The proposal uses `velocity_magnitude < min_velocity`. **This will fail.**
    *   *Reason:* `get_eigenvectors()` returns **unit vectors** (norm = 1.0). The "velocity" never drops near singularities; the direction just becomes unstable.
    *   *Fix:* Use **Anisotropy** check. Stop if `anisotropy < threshold` (e.g., 0.1). This correctly identifies isotropic regions (junction centers) where direction is undefined.
2.  **Bidirectional Tracing:** Roads don't have a "flow". Tracing from a seed point only goes "forward".
    *   *Fix:* You must trace **twice** for each seed: once with `+eigenvector` and once with `-eigenvector`, then combine the results.

**Additional Conditions:**
*   **Loop Detection:** Check distance to start point after some length.
*   **Minimum Length:** Discard streamlines shorter than X meters (post-processing).

## 3. Boundary Handling
**Recommended Approach:** **Shapely Polygon with Bounding Box Optimization**
**Performance Impact:** Shapely is fast enough for O(1000) steps.
**Implementation Guidance:**
```python
# Optimization: Check bbox first (very fast)
if not (xmin <= x <= xmax and ymin <= y <= ymax):
    break
# Then check precise polygon
if not self.boundary.contains(Point(x, y)):
    break
```

## 4. Seed Point Strategy
**Recommended Strategy:** **Anisotropy-Weighted Grid**
**Rationale:** Don't seed in junctions (low anisotropy) or empty space.
**Implementation:**
1.  Create a coarse grid of candidate points.
2.  Compute `anisotropy` for all candidates (vectorized).
3.  Filter: Keep points where `anisotropy > 0.5` (clear direction).
4.  (Optional) Sort by anisotropy descending to prioritize main roads.

## 5. Data Structure
**Recommended Format:** `List[np.ndarray]` (List of LineStrings)
**Essential Export:** **GeoJSON**
**Rationale:**
*   Web-native (Mapbox/Leaflet ready).
*   Human-readable debugging.
*   Easy to convert to other formats.

## 6. Validation Strategy
**Metrics to Compute:**
*   **Total Network Length:** Sum of all road lengths.
*   **Junction Count:** Number of streamline endpoints that terminate due to "Singularity" (Anisotropy check).

**Visual Checks:**
*   Overlay generated lines on top of the `streamplot` from Day 2. They should align perfectly.

## 7. Implementation Readiness
**Overall Assessment:** **Needs Revisions**
**Go/No-Go:** 🟡 **YELLOW** - Proceed with critical fixes (Singularity Check & Bidirectional Tracing).

## 8. Critical Implementation Instructions

**Must-Have Features:**
1.  **Fix Singularity Check:** Use `tensor_field.get_anisotropy(point) < threshold` to stop integration. Do NOT use velocity magnitude.
2.  **Bidirectional Tracing:** Implement a wrapper that traces forward and backward from the seed, then concatenates: `road = reverse(backward_trace) + forward_trace`.
3.  **Step-by-Step Loop:** Use `while solver.status == 'running':` loop to allow per-step checks.

**Code Snippets (Corrected Trace Loop):**
```python
# Inside trace()
while solver.status == 'running':
    solver.step()
    current_point = solver.y
    
    # 1. Boundary Check
    if not self._is_within_boundary(current_point):
        break
        
    # 2. Singularity Check (Anisotropy)
    # Note: This requires a single-point anisotropy check method
    aniso = self.tensor_field.get_anisotropy(current_point.reshape(1, 2))[0]
    if aniso < min_anisotropy:
        break
        
    points.append(current_point)
```

**Testing Priorities:**
1.  `test_trace_stops_at_boundary`: Verify boundary clipping.
2.  `test_trace_stops_at_junction`: Verify anisotropy stopping condition.
3.  `test_bidirectional_tracing`: Ensure roads grow in both directions from seed.
