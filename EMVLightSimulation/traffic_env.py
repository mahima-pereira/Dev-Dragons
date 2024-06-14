import gym
from gym import spaces
import numpy as np

class TrafficEnv(gym.Env):
    def __init__(self, num_intersections):
        super(TrafficEnv, self).__init__()
        self.num_intersections = num_intersections
        self.action_space = spaces.Discrete(8)  # 8 possible traffic signal phases
        self.observation_space = spaces.Box(low=0, high=100, shape=(num_intersections, 4), dtype=np.float32)

        self.state = None
        self.reset()

    def reset(self):
        self.state = np.random.uniform(0, 100, (self.num_intersections, 4))  # Random initial state
        return self.state

    def step(self, action):
        next_state = self.state.copy()
        reward = 0
        done = False

        # Simulate traffic update based on action (simplified)
        for i in range(self.num_intersections):
            next_state[i, action % 4] -= 1  # Random traffic light action effect
            next_state[i] = np.clip(next_state[i], 0, 100)

        for i in range(self.num_intersections):
            reward -= self.calculate_pressure(i)

        self.state = next_state
        return next_state, reward, done, {}

    def calculate_pressure(self, intersection_id):
        incoming_vehicles = np.sum(self.state[intersection_id, :2])
        outgoing_vehicles = np.sum(self.state[intersection_id, 2:])
        return incoming_vehicles - outgoing_vehicles

# Example usage:
if __name__ == "__main__":
    env = TrafficEnv(num_intersections=4)
    state = env.reset()
    action = env.action_space.sample()
    next_state, reward, done, info = env.step(action)
    print(f"Next State: {next_state}, Reward: {reward}")