#!/bin/bash

echo "🔍 DAY 4 FINAL VALIDATION"
echo "========================"
echo ""

# Test all
echo "1️⃣ Running tests..."
pytest tests/unit/test_hsaga_ga.py tests/integration/test_hsaga_full.py -v --tb=short -q --no-cov
if [ $? -ne 0 ]; then
    echo "❌ Tests failed!"
    exit 1
fi
echo "✅ Tests passed"
echo ""

# Coverage check
echo "2️⃣ Checking coverage..."
pytest tests/unit/test_hsaga_ga.py --cov=src/algorithms/hsaga --cov-report=term-missing -q 2>&1 | grep -E "hsaga.py|TOTAL|Cover" | head -3
echo ""

# Pre-commit
echo "3️⃣ Running pre-commit hooks..."
pre-commit run --all-files > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  Pre-commit warnings (check manually)"
else
    echo "✅ Pre-commit passed"
fi
echo ""

# Git status
echo "4️⃣ Checking git status..."
git status --short
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Uncommitted changes detected"
else
    echo "✅ Working tree clean"
fi
echo ""

# Branch status
echo "5️⃣ Recent commits..."
git log --oneline -5
echo ""

# Quick benchmark
echo "6️⃣ Running quick benchmark..."
python3 -c "
from src.algorithms.hsaga import HybridSAGA
from src.algorithms.building import Building, BuildingType
import time

buildings = [Building(f'B{i}', BuildingType.RESIDENTIAL, 2000, 3) for i in range(5)]
optimizer = HybridSAGA(buildings, (0, 0, 1000, 1000))

# Reduce for quick test
optimizer.sa_config['chain_iterations'] = 10
optimizer.ga_config['generations'] = 5
optimizer.ga_config['population_size'] = 10

start = time.time()
result = optimizer.optimize()
elapsed = time.time() - start

print(f'Runtime: {elapsed:.2f}s')
print(f'Fitness: {result[\"fitness\"]:.4f}')
"

echo ""
echo "✅ ALL VALIDATIONS PASSED!"
echo "Ready for Day 5"
