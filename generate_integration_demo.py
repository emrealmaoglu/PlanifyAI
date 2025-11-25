
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon
from backend.core.integration import CompositeGenotype, TensorFieldParams, BuildingLayout, visualize_integrated_layout

def generate_demo():
    # Define boundary
    boundary = Polygon([(0, 0), (500, 0), (500, 500), (0, 500)])
    
    # Create random params
    tensor_params = TensorFieldParams(
        grid_centers=np.array([[150, 150], [350, 350]]),
        grid_orientations=np.array([0, np.pi/4]),
        grid_decay_radii=np.array([200, 200]),
        radial_centers=np.array([[250, 250]]),
        radial_decay_radii=np.array([150])
    )
    
    # Random buildings
    n_buildings = 20
    positions = np.random.rand(n_buildings, 2) * 400 + 50
    types = np.random.randint(0, 5, n_buildings)
    orientations = np.random.rand(n_buildings) * np.pi
    
    building_layout = BuildingLayout(
        positions=positions,
        types=types,
        orientations=orientations
    )
    
    genotype = CompositeGenotype(tensor_params, building_layout)
    
    print("Decoding genotype...")
    roads, buildings = genotype.decode(boundary)
    print(f"Generated {len(roads)} road segments and {len(buildings)} buildings.")
    
    print("Visualizing...")
    fig = visualize_integrated_layout(
        roads, buildings, boundary, 
        tensor_field=tensor_params.to_tensor_field(),
        title="Phase 3 Milestone 1: Integration Demo"
    )
    
    output_path = "/tmp/integration_demo.png"
    fig.savefig(output_path)
    print(f"Saved visualization to {output_path}")

if __name__ == "__main__":
    generate_demo()
