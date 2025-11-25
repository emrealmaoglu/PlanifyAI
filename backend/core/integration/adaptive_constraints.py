class AdaptiveConstraintHandler:
    """Gradually enforce constraints using epsilon-constraint method."""
    
    def __init__(self, initial_epsilon=100.0, decay_rate=0.9):
        self.epsilon = initial_epsilon
        self.decay_rate = decay_rate
        self.generation = 0
    
    def update(self):
        """Decay epsilon each generation."""
        self.epsilon *= self.decay_rate
        self.generation += 1
    
    def apply_penalty(self, constraint_violation):
        """Apply adaptive penalty based on current epsilon."""
        if constraint_violation <= self.epsilon:
            # Within tolerance - small penalty
            return constraint_violation * 0.1
        else:
            # Outside tolerance - increasing penalty
            excess = constraint_violation - self.epsilon
            return self.epsilon * 0.1 + excess * 10.0
