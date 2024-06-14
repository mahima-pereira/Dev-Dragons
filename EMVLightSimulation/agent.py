import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

class PolicyNetwork(nn.Module):
    def __init__(self, state_dim, action_dim):
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(state_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        self.lstm = nn.LSTM(64, 64)
        self.fc3 = nn.Linear(64, action_dim)

    def forward(self, x, hidden):
        x = x.flatten()  # Flatten the input tensor
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = x.unsqueeze(0)  # Add batch dimension
        x, hidden = self.lstm(x.unsqueeze(0), hidden)
        x = self.fc3(x.squeeze(0))  # Remove batch dimension
        return torch.softmax(x, dim=-1), hidden

class ValueNetwork(nn.Module):
    def __init__(self, state_dim):
        super(ValueNetwork, self).__init__()
        self.fc1 = nn.Linear(state_dim, 128)
        self.fc2 = nn.Linear(128, 64)
        self.lstm = nn.LSTM(64, 64)
        self.fc3 = nn.Linear(64, 1)

    def forward(self, x, hidden):
        x = x.flatten()  # Flatten the input tensor
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = x.unsqueeze(0)  # Add batch dimension
        x, hidden = self.lstm(x.unsqueeze(0), hidden)
        x = self.fc3(x.squeeze(0))  # Remove batch dimension
        return x, hidden


class Agent:
    def __init__(self, state_dim, action_dim, lr=1e-3, batch_size=1):
        self.policy_net = PolicyNetwork(state_dim, action_dim)
        self.value_net = ValueNetwork(state_dim)
        self.optimizer_policy = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.optimizer_value = optim.Adam(self.value_net.parameters(), lr=lr)
        self.batch_size = batch_size
        self.hidden = (torch.zeros(1, batch_size, 64), torch.zeros(1, batch_size, 64))

    def select_action(self, state):
        state = torch.tensor(state, dtype=torch.float32)
        probs, self.hidden = self.policy_net(state, self.hidden)
        m = Categorical(probs)
        action = m.sample()
        return action.item(), m.log_prob(action)

    def compute_loss(self, log_probs, values, rewards):
        Qvals = []
        Qval = 0
        for r in reversed(rewards):
            Qval = r + 0.99 * Qval
            Qvals.insert(0, Qval)

        Qvals = torch.tensor(Qvals, dtype=torch.float32)
        log_probs = torch.stack(log_probs)
        values = torch.stack(values).squeeze(-1)

        advantage = Qvals - values

        actor_loss = (-log_probs * advantage.detach()).mean()
        critic_loss = advantage.pow(2).mean()

        return actor_loss + critic_loss

    def update(self, log_probs, values, rewards):
        loss = self.compute_loss(log_probs, values, rewards)
        self.optimizer_policy.zero_grad()
        self.optimizer_value.zero_grad()
        loss.backward()
        self.optimizer_policy.step()
        self.optimizer_value.step()