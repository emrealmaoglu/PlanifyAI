from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.surrogate.data_generator import SurrogateDataGenerator
from backend.core.integration.surrogate.trainer import SurrogateTrainer
from shapely.geometry import Polygon
import os

if __name__ == "__main__":
    # Ensure directories exist
    os.makedirs("data/surrogate", exist_ok=True)
    
    # Generate training data
    boundary = Polygon([(0,0),(1000,0),(1000,1000),(0,1000)])
    
    print("Initializing problem...")
    problem = IntegratedCampusProblem(
        boundary=boundary, n_buildings=50,
        objectives=['cost','adjacency','road_access','walkability'],
        enable_turkish_standards=True
    )
    
    print("Generating training data...")
    # Use fewer samples for quick testing if needed, but 1000 for production
    generator = SurrogateDataGenerator(problem, n_samples=50)
    data = generator.generate()
    
    # Train models
    print("Training surrogate models...")
    data_path = f"data/surrogate/training_data_50.pkl"
    trainer = SurrogateTrainer(data_path)
    
    # Train for expensive objectives
    models, metrics = trainer.train_all(['road_access', 'walkability'])
    
    trainer.save_models(models, 'data/surrogate/models.pkl')
    print("\nTraining complete!")
