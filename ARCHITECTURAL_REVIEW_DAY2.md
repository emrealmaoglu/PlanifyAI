# Architectural Review Report: TensorField Blending

## 1. Mathematical Correctness
The core concept of **Gaussian-weighted tensor averaging** is mathematically sound for this application.

*   **Symmetry Preservation:** A linear combination of symmetric matrices with positive weights is always symmetric. This guarantees real eigenvalues and orthogonal eigenvectors, which is critical for extracting valid road directions.
*   **Positive Definiteness:** Since basis fields produce Positive Semi-Definite (PSD) tensors (e.g., outer products $v \otimes v$ or rotated diagonal matrices with positive entries), their weighted sum is also PSD. This ensures the "energy" or "importance" of the field remains positive.
*   **Eigenvector Blending:** Blending tensors correctly interpolates the *orientation* and *anisotropy* (strength of direction), unlike vector averaging which can cancel out opposing vectors.

**Verdict:** ✅ **Sound**
**Recommendations:** Ensure `GridField` produces strictly positive eigenvalues (e.g., 1.0 and 0.1, not 1.0 and 0.0) to avoid degenerate tensors in the blend, which helps numerical stability.

## 2. Edge Case Handling
The design anticipates most issues, but "Isotropic Points" need specific attention.

*   **All weights near zero:** The fallback to `np.eye(2)` is a safe and correct default (implies no preferred direction, effectively a grid).
*   **Competing Fields (The "Cross" Case):** If two orthogonal fields ($0^\circ$ and $90^\circ$) have equal weight, the average tensor is $\propto I$ (Identity).
    *   *Result:* The tensor becomes isotropic (circle). Eigenvalues are equal.
    *   *Consequence:* `eigh` will return arbitrary orthogonal vectors.
    *   *Fix:* This is mathematically correct (it's a junction/plaza). No "fix" needed, but the streamline tracer (in later steps) must handle these singularities gracefully (e.g., by stopping or branching).
*   **Radial Singularity:** At the exact center, the radial vector is zero. The `RadialField` implementation should ensure it returns a valid tensor (e.g., isotropic or zero) rather than NaNs.

**Critical Issues:** None.
**Proposed Fixes:** Ensure `RadialField` handles $r=0$ (already done in Day 1).

## 3. Performance Analysis
The **vectorized approach** is mandatory and correctly designed.

*   **Complexity:** The vectorized version reduces Python overhead from $O(F \times N)$ to $O(F)$. For $N=10,000$ points, this is orders of magnitude faster.
*   **Memory:** Creating `(N, 2, 2)` arrays is memory-efficient enough for reasonable $N$.
*   **M1 Optimization:** NumPy on M1 (Accelerate backend) is highly optimized for matrix operations. `np.linalg.eigh` is vectorized and efficient.

**Verdict:** ✅ **Optimal**
**M1-Specific Recommendations:** Ensure `numpy` is linked to Accelerate (standard on macOS arm64 wheels).

## 4. Eigenvector Extraction
`np.linalg.eigh` is the correct choice.

*   **Why:** It is specialized for Hermitian/symmetric matrices. It guarantees real eigenvalues and orthogonal eigenvectors.
*   **Ordering:** It returns eigenvalues in ascending order.
    *   Minor eigenvector = index 0
    *   Major eigenvector = index 1
*   **Stability:** More stable than `eig` for symmetric inputs.

**Recommended Approach:** `np.linalg.eigh`

## 5. Testing Strategy
The proposed tests are strong. I recommend adding a specific test for the "Isotropic/Crossing" case.

**Tests to Add:**
1.  `test_orthogonal_crossing`: Blend two equal-strength orthogonal grids. Assert eigenvalues are approximately equal (anisotropy $\approx$ 0).
2.  `test_vectorization_match`: Verify that the vectorized implementation matches the loop-based reference (for correctness confidence).
3.  `test_degenerate_fallback`: Explicitly test points far from all fields.

**Priority Tests:**
1.  `test_eigenvector_orthogonality` (Sanity check)
2.  `test_field_smoothness` (Visual or numerical gradient check)
3.  `test_zero_weight_fallback`

## 6. Visualization Validation
Quiver plots are good, but **Streamlines** are better for road networks.

**Verdict:** ⚠️ **Needs Enhancement**
**Additional Visualizations:**
*   **Streamplot:** Use `plt.streamplot` to visualize the continuous flow lines. This mimics how the road generation algorithm (hyperstreamlines) will actually work.
*   **Anisotropy Heatmap:** Plot the ratio of eigenvalues ($\lambda_1 / \lambda_2$). High values = clear direction (road). Low values ($\approx 1$) = junctions/plazas.

## 7. Implementation Readiness
**Overall Assessment:** **Ready**
The architecture is well-thought-out, mathematically valid, and performance-aware.

**Go/No-Go Decision:** ✅ **GREEN** - Proceed with implementation.

## 8. Specific Instructions for Implementation

**Critical Changes:**
1.  **Implement Vectorized Only:** Do not implement the loop-based version. Go straight to the vectorized implementation for `get_blended_tensor`.
2.  **Anisotropy Helper:** Add a method `get_anisotropy(points)` to the `TensorField` class. It helps in debugging and visualization.
    *   Formula: $1 - (\lambda_{min} / \lambda_{max})$ or similar metric.

**Optional Enhancements:**
1.  **Streamline Visualization Method:** Add a `visualize(points)` method to the class that automatically generates the quiver and streamplot.

**Code Snippets (Vectorized Blend):**
```python
def get_blended_tensor(self, points: np.ndarray) -> np.ndarray:
    N = points.shape[0]
    blended = np.zeros((N, 2, 2))
    total_weights = np.zeros(N)
    
    for field in self.basis_fields:
        # (N, 2, 2)
        tensors = field.get_tensor(points)
        # (N,)
        weights = field.get_weight(points)
        
        # Broadcasting: (N, 1, 1) * (N, 2, 2)
        blended += weights[:, None, None] * tensors
        total_weights += weights
    
    # Avoid division by zero
    mask = total_weights > 1e-6
    
    # Normalize valid points
    # (N_valid, 2, 2) / (N_valid, 1, 1)
    blended[mask] /= total_weights[mask, None, None]
    
    # Fallback for empty space -> Identity
    blended[~mask] = np.eye(2)
    
    return blended
```
