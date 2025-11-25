"""Integration test: 5-field campus layout."""

import numpy as np
from backend.core.spatial.basis_fields import GridField, RadialField
from backend.core.spatial.tensor_field import TensorField


def test_five_field_campus_layout():
    """
    End-to-end test: Realistic 5-field campus.

    This tests the complete tensor field pipeline with a
    configuration that mimics a real campus layout.
    """
    # Create 5-field layout (as in Gemini review)
    fields = [
        GridField((250, 250), 50, theta=0, decay_radius=150),  # Main axis
        GridField((400, 400), 50, theta=np.pi / 2, decay_radius=100),  # Cross axis
        RadialField((100, 100), decay_radius=120),  # Junction 1
        RadialField((700, 700), decay_radius=120),  # Junction 2
        GridField((500, 300), 50, theta=np.pi / 4, decay_radius=80),  # Diagonal
    ]

    tensor_field = TensorField(fields)

    # Generate test grid (800×800 campus)
    x = np.linspace(0, 800, 50)
    y = np.linspace(0, 800, 50)
    X, Y = np.meshgrid(x, y)
    points = np.c_[X.ravel(), Y.ravel()]

    # 1. Test blending works
    tensors = tensor_field.get_blended_tensor(points)
    assert tensors.shape == (2500, 2, 2)
    assert np.all(np.isfinite(tensors))

    # 2. Test eigenvectors are valid
    major_vectors = tensor_field.get_eigenvectors(points, "major")
    assert major_vectors.shape == (2500, 2)

    # All vectors should be unit length
    norms = np.linalg.norm(major_vectors, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-6)

    # 3. Test anisotropy is computed
    anisotropy = tensor_field.get_anisotropy(points)
    assert anisotropy.shape == (2500,)
    assert np.all((anisotropy >= 0) & (anisotropy <= 1))

    # 4. Visual validation (creates plot for manual inspection)
    fig = tensor_field.visualize(
        bbox=(0, 0, 800, 800), resolution=40, show_anisotropy=True, show_streamplot=True
    )

    # Save for thesis/documentation
    fig.savefig("/tmp/tensor_field_5field_campus.png", dpi=150)
    print("✅ Visualization saved to /tmp/tensor_field_5field_campus.png")
