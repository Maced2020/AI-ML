# agent.py
# RL agent logic (DQN)

import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from config import ACTIONS

class DQN(nn.Module):
    def __init__(self, input_shape, n_actions):
        super().__init__()
        self.model = nn.Sequential(
            nn.Conv2d(1, 32, 8, stride=4),
            nn.ReLU(),
            nn.Conv2d(32, 64, 4, stride=2),
            nn.ReLU(),
            nn.Conv2d(64, 64, 3, stride=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(64 * 7 * 7, 512),
            nn.ReLU(),
            nn.Linear(512, n_actions)
        )

    def forward(self, x):
        return self.model(x)

class Agent:
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = DQN((1, 84, 84), len(ACTIONS)).to(self.device)
        self.target = DQN((1, 84, 84), len(ACTIONS)).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-4)
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.1

    def select_action(self, state, available_actions):
        if np.random.rand() < self.epsilon:
            return np.random.randint(len(available_actions))

        state = torch.tensor(state, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(self.device)
        q_values = self.model(state)

        # Map full Q-values to available_actions only
        full_q_values = q_values[0].detach().cpu().numpy()
        indices = [ACTIONS.index(a) for a in available_actions]
        filtered_q_values = full_q_values[indices]

        return int(np.argmax(filtered_q_values))

    def train_step(self, buffer, batch_size=32):
        if len(buffer) < batch_size:
            return

        states, actions, rewards, next_states, dones = buffer.sample(batch_size)
        states = torch.tensor(states, dtype=torch.float32).unsqueeze(1).to(self.device)
        next_states = torch.tensor(next_states, dtype=torch.float32).unsqueeze(1).to(self.device)
        actions = torch.tensor(actions, dtype=torch.int64).unsqueeze(1).to(self.device)
        rewards = torch.tensor(rewards, dtype=torch.float32).unsqueeze(1).to(self.device)
        dones = torch.tensor(dones, dtype=torch.float32).unsqueeze(1).to(self.device)

        q_values = self.model(states).gather(1, actions)
        with torch.no_grad():
            target_q = self.target(next_states).max(1)[0].unsqueeze(1)
            target = rewards + (1 - dones) * self.gamma * target_q

        loss = nn.functional.mse_loss(q_values, target)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)

    def update_target(self):
        self.target.load_state_dict(self.model.state_dict())

    def save_model(self, path="models/dqn_model.pth"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save(self.model.state_dict(), path)
        print(f"✅ Model saved to {path}")

    def load_model(self, path="models/dqn_model.pth"):
        if os.path.exists(path):
            self.model.load_state_dict(torch.load(path, map_location=self.device))
            self.update_target()
            print(f"📦 Loaded model from {path}")
        else:
            print(f"⚠️ No model found at {path}, starting fresh.")
