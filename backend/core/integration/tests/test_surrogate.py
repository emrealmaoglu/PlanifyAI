import pytest
import numpy as np
from shapely.geometry import Polygon
from backend.core.integration import IntegratedCampusProblem
from backend.core.integration.surrogate.data_generator import SurrogateDataGenerator
from backend.core.integration.surrogate.trainer import SurrogateTrainer
from backend.core.integration.surrogate.evaluator import SurrogateAssistedEvaluator
import os
import pickle

@pytest.fixture
def problem():
    boundary = Polygon([(0,0),(100,0),(100,100),(0,100)])
    return IntegratedCampusProblem(
        boundary=boundary, n_buildings=5,
        objectives=['cost','adjacency'],
        enable_turkish_standards=False
    )

def test_data_generation(problem, tmp_path):
    output_dir = tmp_path / "surrogate"
    generator = SurrogateDataGenerator(problem, n_samples=5, output_dir=output_dir)
    data = generator.generate()
    
    assert data['X'].shape == (5, 10) # 10 features
    assert 'cost' in data['y']
    assert len(data['y']['cost']) == 5
    assert (output_dir / "training_data_5.pkl").exists()

def test_model_training(problem, tmp_path):
    # Generate data first
    output_dir = tmp_path / "surrogate"
    generator = SurrogateDataGenerator(problem, n_samples=10, output_dir=output_dir)
    generator.generate()
    
    data_path = output_dir / "training_data_10.pkl"
    trainer = SurrogateTrainer(data_path)
    
    model, metrics = trainer.train('cost', n_estimators=10)
    
    assert model is not None
    assert 'r2' in metrics
    assert 'mae' in metrics

def test_surrogate_evaluation(problem, tmp_path):
    # Mock models
    class MockModel:
        def predict(self, X):
            return np.random.rand(X.shape[0])
            
    models = {'cost': MockModel()}
    
    evaluator = SurrogateAssistedEvaluator(problem, models, threshold=0.5)
    
    X = np.random.rand(10, problem.n_var)
    X = X * (problem.xu - problem.xl) + problem.xl
    
    result = evaluator.evaluate(X)
    
    assert result['F'].shape == (10, problem.n_obj)
    assert result['G'].shape == (10, problem.n_constr)
